#!/usr/bin/env python3
"""Map-reduce book distillation via the local `claude` CLI.

Uses the user's existing Claude Code auth (OAuth / keychain) instead of an
ANTHROPIC_API_KEY. Each call shells out to `claude -p` with a fresh,
non-persisted session and a custom system prompt.

Subcommands:
  distill.py map <chunks.json> [mapped.json]
  distill.py reduce <mapped.json> [output_dir]
"""
import asyncio
import json
import re
import shutil
import sys
from pathlib import Path

MAP_MODEL = "claude-sonnet-4-6"
REDUCE_MODEL = "claude-opus-4-7"
MAX_CONCURRENCY = 5

MAP_SYSTEM = """You are a careful reader extracting structured insight from one section of a book.

Return STRICT JSON only (no prose, no markdown fence) with this shape:
{
  "thesis": "1-2 sentence section thesis",
  "key_ideas": [
    {"heading": "short title (<=8 words)", "explanation": "2-4 sentences"}
  ],
  "examples": ["concrete examples / case studies / data the section uses"],
  "notable_quotes": [{"quote": "...", "context": "why it matters"}],
  "section_notes": "1-2 paragraphs of additional notes worth keeping"
}

Rules:
- Do NOT cap key_ideas at a fixed number. Extract every substantive idea this section actually develops. A dense section may have 10+; a thin one 1-2.
- An "idea" is a claim, framework, or distinction the author argues for — not a topic mentioned in passing.
- Quote sparingly — only quotes that are memorable or load-bearing.
- Be faithful to the text. Do not invent content.
- Output JSON only. No leading text. No code fences."""

MAP_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "thesis": {"type": "string"},
        "key_ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": ["heading", "explanation"],
            },
        },
        "examples": {"type": "array", "items": {"type": "string"}},
        "notable_quotes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quote": {"type": "string"},
                    "context": {"type": "string"},
                },
                "required": ["quote", "context"],
            },
        },
        "section_notes": {"type": "string"},
    },
    "required": ["thesis", "key_ideas", "examples", "notable_quotes", "section_notes"],
}

REDUCE_SYSTEM = """You are synthesizing chapter-level summaries of a book into a final tiered distillation.

Input: JSON array of section summaries. Output: GitHub-flavored markdown.

Structure exactly:

# <Title> — <Author>

> *One-line thesis of the entire book.*

## Key Ideas

For each distinct idea the book develops, write:

### <Idea heading>
<2-5 sentences: the idea, the argument, why it matters.>
*Appears in: <chapter labels, comma-separated>*

CRITICAL — deduplication and sizing:
- Many sections will restate the same core idea. Merge them. If "compounding habits" appears in 4 chapters, it is ONE key idea, not 4.
- Do NOT enforce a count. Let the book's actual density decide. A focused essay book may yield 6-10 key ideas; a dense philosophy / technical book 25-40+.
- An idea earns its slot only if it adds something the others don't. If you can't articulate the distinction, merge.
- Order key ideas by importance (book's central arguments first), not chapter order.

## Chapter Map

One paragraph per chapter — what the chapter argues, in your own words. Use the chapter label as the paragraph lead-in (bolded).

## Notable Quotes

5-10 of the most memorable or load-bearing quotes from across the book. Format:
> "quote"
> — *chapter label* — 1-line context.

---

Be ruthless about repetition. Be generous about depth on the ideas that earn their place.

Output the markdown directly. No preamble, no code fence."""


def _claude_bin() -> str:
    path = shutil.which("claude")
    if not path:
        sys.exit("error: `claude` CLI not found on PATH. Install Claude Code first.")
    return path


def _parse_json_loose(text: str) -> dict:
    """Tolerate accidental code fences or leading prose."""
    text = text.strip()
    if "```" in text:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


async def _run_claude(
    model: str,
    system_prompt: str,
    user_msg: str,
    *,
    json_schema: dict | None = None,
) -> str | dict:
    """Invoke `claude -p` and return the response.

    Without `json_schema`: returns the assistant's text output (str).
    With `json_schema`: returns the validated structured object (dict).
    """
    args = [
        _claude_bin(),
        "-p",
        "--model", model,
        "--system-prompt", system_prompt,
        "--no-session-persistence",
    ]
    if json_schema is not None:
        # Need --output-format json to surface the structured_output field.
        args += [
            "--json-schema", json.dumps(json_schema),
            "--output-format", "json",
        ]
    else:
        args += ["--output-format", "text"]

    proc = await asyncio.create_subprocess_exec(
        *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(user_msg.encode())
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude CLI exited {proc.returncode}\nstderr: {stderr.decode(errors='replace')[:2000]}"
        )

    out = stdout.decode(errors="replace")
    if json_schema is None:
        return out

    envelope = json.loads(out)
    if envelope.get("is_error"):
        raise RuntimeError(f"claude CLI returned error: {envelope.get('result', '')[:500]}")
    if "structured_output" not in envelope:
        raise RuntimeError(f"no structured_output in response: {out[:500]}")
    return envelope["structured_output"]


async def map_one(chunk: dict, title: str, author: str) -> dict:
    user_msg = f"Book: {title}\nAuthor: {author}\nSection: {chunk['label']}\n\n---\n\n{chunk['text']}"
    try:
        parsed = await _run_claude(MAP_MODEL, MAP_SYSTEM, user_msg, json_schema=MAP_JSON_SCHEMA)
        return {"id": chunk["id"], "label": chunk["label"], **parsed}
    except Exception as e:
        return {
            "id": chunk["id"],
            "label": chunk["label"],
            "error": f"{type(e).__name__}: {e}",
        }


async def run_map(chunks_path: str, out_path: str) -> None:
    data = json.loads(Path(chunks_path).read_text())
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async def worker(chunk: dict) -> dict:
        async with sem:
            print(f"  mapping: {chunk['label'][:60]}", file=sys.stderr)
            return await map_one(chunk, data["title"], data.get("author", ""))

    results = await asyncio.gather(*[worker(c) for c in data["chunks"]])
    errors = sum(1 for r in results if "error" in r)

    Path(out_path).write_text(json.dumps({
        "title": data["title"],
        "author": data.get("author", ""),
        "sections": results,
    }, indent=2))
    print(f"mapped {len(results)} sections → {out_path} ({errors} errors)")


async def run_reduce(mapped_path: str, out_dir: str) -> str:
    data = json.loads(Path(mapped_path).read_text())
    title = data["title"]
    author = data.get("author", "")

    sections = [{k: v for k, v in s.items() if k != "raw"} for s in data["sections"]]
    user_msg = (
        f"Book: {title}\nAuthor: {author}\n\n"
        f"Section summaries (JSON):\n\n{json.dumps(sections, indent=2)}"
    )

    md = await _run_claude(REDUCE_MODEL, REDUCE_SYSTEM, user_msg)

    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    safe = "".join(c for c in title if c.isalnum() or c in " -_").strip().replace(" ", "_")[:80] or "book"
    out_path = out / f"{safe}.md"
    out_path.write_text(md)
    print(f"distillation → {out_path}")
    return str(out_path)


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "usage:\n  distill.py map <chunks.json> [mapped.json]\n  distill.py reduce <mapped.json> [output_dir]",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "map":
        chunks_path = sys.argv[2]
        out_path = sys.argv[3] if len(sys.argv) > 3 else "mapped.json"
        asyncio.run(run_map(chunks_path, out_path))
    elif cmd == "reduce":
        mapped_path = sys.argv[2]
        out_dir = sys.argv[3] if len(sys.argv) > 3 else "~/Documents/book-distills"
        asyncio.run(run_reduce(mapped_path, out_dir))
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
