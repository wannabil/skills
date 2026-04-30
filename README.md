# skills

Personal Claude Code skills, copied from `~/.claude/skills/`. Drop any of these folders into your own `~/.claude/skills/` directory to use them.

## Available skills

### `research/`

Builds a distilled research PDF on any topic. Pulls papers from OpenAlex + ArXiv (free, no API key), ranks by citations × recency, and synthesizes into a structured PDF.

### `frontend-design/`

Research-driven Next.js + Tailwind page builder. Defaults to category research (top-5 reference sites, screenshot, synthesize, build), with a **reference-site mode** for when the user names a single site to copy:

- **Close-clone mode** (default for "copy X" / "like X") — match the reference's layout, palette, type scale, section rhythm, and imagery style; replace brand, copy, logos, and photos with originals.
- **User-owned rebuild mode** (1:1) — for when the user owns the site, do a faithful re-platform with same brand, copy, and imagery.

See [`frontend-design/examples/`](./frontend-design/examples/) for a sample run.
