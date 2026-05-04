#!/usr/bin/env python3
"""Extract text and TOC from a PDF/EPUB into chunks.json.

Output JSON shape:
{
  "title": str, "author": str,
  "chunks": [{ "id": int, "label": str, "text": str, "page_range": [start, end] | null }]
}

Chunking strategy:
- PDF with usable top-level outline (>=3 entries) → one chunk per outline entry.
- EPUB → one chunk per spine document (skipping tiny ones).
- Otherwise → fixed 8k-token chunks with 500-token overlap.
"""
import json
import sys
from pathlib import Path


TARGET_TOKENS = 8000
OVERLAP_TOKENS = 500
CHARS_PER_TOKEN = 4  # rough


def fixed_chunks(full_text: str) -> list[dict]:
    target = TARGET_TOKENS * CHARS_PER_TOKEN
    overlap = OVERLAP_TOKENS * CHARS_PER_TOKEN
    chunks, pos, i = [], 0, 0
    while pos < len(full_text):
        end = min(pos + target, len(full_text))
        chunks.append({
            "id": i,
            "label": f"Section {i + 1}",
            "text": full_text[pos:end],
            "page_range": None,
        })
        if end >= len(full_text):
            break
        pos = end - overlap
        i += 1
    return chunks


def extract_pdf(path: str) -> dict:
    import pdfplumber
    from pypdf import PdfReader

    title = Path(path).stem
    author = ""

    with pdfplumber.open(path) as pdf:
        meta = pdf.metadata or {}
        title = (meta.get("Title") or title).strip() or title
        author = (meta.get("Author") or "").strip()
        page_texts = [(p.extract_text() or "") for p in pdf.pages]

    if not any(t.strip() for t in page_texts):
        print("warning: no text extracted — PDF may be scanned. Run `ocrmypdf` first.", file=sys.stderr)

    reader = PdfReader(path)
    outline_flat: list[tuple[str, int, int]] = []

    def walk(items, depth=0):
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
            else:
                try:
                    page = reader.get_destination_page_number(item)
                    outline_flat.append((str(item.title), page, depth))
                except Exception:
                    continue

    try:
        walk(reader.outline)
    except Exception:
        outline_flat = []

    top = [o for o in outline_flat if o[2] == 0]
    chunks: list[dict] = []
    if len(top) >= 3:
        for i, (label, start, _) in enumerate(top):
            end = top[i + 1][1] if i + 1 < len(top) else len(page_texts)
            text = "\n\n".join(page_texts[start:end]).strip()
            if text:
                chunks.append({
                    "id": i,
                    "label": label,
                    "text": text,
                    "page_range": [start + 1, end],
                })
    else:
        chunks = fixed_chunks("\n\n".join(page_texts))

    return {"title": title, "author": author, "chunks": chunks}


def extract_epub(path: str) -> dict:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup

    book = epub.read_epub(path)
    title_meta = book.get_metadata("DC", "title")
    author_meta = book.get_metadata("DC", "creator")
    title = title_meta[0][0] if title_meta else Path(path).stem
    author = author_meta[0][0] if author_meta else ""

    chunks: list[dict] = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        text = soup.get_text(separator="\n").strip()
        if len(text) < 200:
            continue
        first_line = text.split("\n", 1)[0].strip()
        label = first_line[:80] if first_line else f"Section {len(chunks) + 1}"
        chunks.append({
            "id": len(chunks),
            "label": label,
            "text": text,
            "page_range": None,
        })

    if not chunks:
        # very rare — fall back to one big concatenation chunked fixed
        full = ""
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            full += BeautifulSoup(item.get_content(), "html.parser").get_text("\n") + "\n\n"
        chunks = fixed_chunks(full.strip())

    return {"title": title, "author": author, "chunks": chunks}


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: extract.py <book.pdf|book.epub> [output.json]", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "chunks.json"

    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        data = extract_pdf(path)
    elif ext == ".epub":
        data = extract_epub(path)
    else:
        print(f"unsupported extension: {ext}", file=sys.stderr)
        sys.exit(1)

    Path(out).write_text(json.dumps(data, indent=2))
    total_chars = sum(len(c["text"]) for c in data["chunks"])
    est_tokens = total_chars // CHARS_PER_TOKEN
    print(
        f"wrote {out}: {len(data['chunks'])} chunks, "
        f"~{est_tokens:,} tokens, title={data['title']!r}"
    )


if __name__ == "__main__":
    main()
