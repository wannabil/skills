#!/usr/bin/env python3
"""Convert a book-distill markdown file into an Anki .apkg deck.

Cards are built from the "## Key Ideas" section: front = idea heading,
back = explanation + chapter attribution.
"""
import re
import sys
from pathlib import Path


def parse_distill(md_text: str) -> tuple[str, list[tuple[str, str]]]:
    title_match = re.search(r"^# (.+?)$", md_text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Book"

    ki_match = re.search(r"## Key Ideas\s*\n(.+?)(?=\n## |\Z)", md_text, re.DOTALL)
    if not ki_match:
        return title, []

    body = ki_match.group(1)
    cards: list[tuple[str, str]] = []
    for m in re.finditer(r"### (.+?)\n(.+?)(?=\n### |\Z)", body, re.DOTALL):
        heading = m.group(1).strip()
        explanation = m.group(2).strip()
        cards.append((heading, explanation))
    return title, cards


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: anki_export.py <distill.md> [out.apkg]", file=sys.stderr)
        sys.exit(1)

    md_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else md_path.with_suffix(".apkg")

    title, cards = parse_distill(md_path.read_text())
    if not cards:
        print("no key ideas found in markdown", file=sys.stderr)
        sys.exit(1)

    try:
        import genanki
    except ImportError:
        print("install genanki: pip install genanki", file=sys.stderr)
        sys.exit(1)

    model = genanki.Model(
        1607392319,
        "Book Distill",
        fields=[{"name": "Front"}, {"name": "Back"}],
        templates=[{
            "name": "Card 1",
            "qfmt": "{{Front}}",
            "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
        }],
    )

    deck_id = abs(hash(title)) % (10 ** 9)
    deck = genanki.Deck(deck_id, title)

    for front, back in cards:
        html_back = back.replace("\n", "<br>")
        deck.add_note(genanki.Note(model=model, fields=[front, html_back]))

    genanki.Package(deck).write_to_file(str(out_path))
    print(f"deck → {out_path} ({len(cards)} cards)")


if __name__ == "__main__":
    main()
