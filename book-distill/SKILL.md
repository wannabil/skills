---
name: book-distill
description: Distill a long book (PDF/EPUB) into a tiered markdown summary — thesis, key ideas, chapter map, notable quotes — using a map-reduce pipeline (Sonnet for chapter summaries, Opus for synthesis). Use when the user wants to compress a book into digestable notes ("distill this book", "summarize this 400-page PDF", "give me the key ideas from <book>"). Anki deck export is a separate optional follow-up.
---

# Book Distill

## When invoked

User wants to compress a book or long document into structured notes.

## Inputs

1. Path to a `.pdf` or `.epub` file the user owns or has rights to read.
2. Optional output directory (default `~/Documents/book-distills/`).

If no path is supplied, ask once. **Never** download from z-library, libgen, or other piracy sources — direct the user to provide their own file or a public-domain title (Project Gutenberg, Standard Ebooks).

## Workflow

Run from the skill directory: `cd ~/.claude/skills/book-distill`.

Uses the local `claude` CLI for all LLM calls (your existing Claude Code auth — no `ANTHROPIC_API_KEY` needed). Each call is a fresh `claude -p --no-session-persistence` subprocess with a custom `--system-prompt`. Deps installed via `pip install -r requirements.txt` (or `uv pip install -r requirements.txt`); the `anthropic` SDK is no longer required for distill (still used by `anki_export.py`).

### 1. Extract & chunk

```
python scripts/extract.py "<book.pdf>" /tmp/chunks.json
```

Produces JSON with `title`, `author`, `chunks[]`. Chunks come from the PDF outline / EPUB spine when available; otherwise fixed 8k-token chunks with 500-token overlap.

### 2. Map (parallel chapter summaries)

```
python scripts/distill.py map /tmp/chunks.json /tmp/mapped.json
```

For each chunk, spawns `claude -p --model claude-sonnet-4-6` with the map system prompt and `--json-schema` for structured output. Extracts thesis, key ideas (no count cap), examples, quotes, notes. Max 5 concurrent.

### 3. Reduce (synthesize)

```
python scripts/distill.py reduce /tmp/mapped.json ~/Documents/book-distills
```

Single Opus 4.7 call. Output markdown structure:

- **Thesis** — 1 line
- **Key Ideas** — every distinct substantive idea, deduped semantically. **No fixed count.** Density of the book determines it (a focused essay book may yield 6–10; a dense philosophy/technical book 25–40+). Each idea: short heading + 2–5 sentence explanation + chapters where it appears.
- **Chapter Map** — 1 paragraph per chapter
- **Notable Quotes** — 5–10 across the book

### 4. Report

Print the path to the markdown file. Mention Anki export is available as a separate command if the user wants flashcards (do NOT run it by default):

```
python scripts/anki_export.py <distill.md>
```

## Key constraints (bake into the reduce prompt)

- **Do not enforce a key-idea count.** Let book density decide.
- **Dedupe ruthlessly.** Authors restate ideas across chapters; surface each idea once. If two ideas are restatements, merge.
- **Each idea earns its slot only if it adds something the others don't.**
- Order by importance (book's central arguments first), not chapter order.

## Cost / billing

Calls go through your local `claude` session, so usage is billed against whatever plan that session uses (Max plan / API key / etc.). A 500-page book is ≈ 165k input tokens across the map phase + one Opus reduce pass.

## Failure modes

- No usable TOC → fixed chunks (already handled).
- Scanned PDF (no text layer) → extract.py warns; user needs OCR first (`ocrmypdf input.pdf output.pdf`).
- Section JSON parse error in map phase → that section's `error` + `raw` fields surface in mapped.json; reduce phase tolerates them but flag to the user so they can rerun if needed.
