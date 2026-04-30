---
name: research
description: Build a distilled research PDF (15/20/30/50pp or custom) on any topic. Pulls papers from OpenAlex + ArXiv (free, no API key), ranks by citations × recency, synthesizes into a structured PDF, and weaves in code snippets, formulas, and diagrams where they aid understanding.
---

# /research — structured topic distillation

When invoked, behave as a thorough research librarian who refuses to fetch anything until the user's knowledge inquiry is genuinely understood.

## 1. Clarification phase (MANDATORY before fetching)

Use `AskUserQuestion` repeatedly. Do not batch all questions into one form — fire them one or two at a time, and let answers shape follow-ups. Continue until you can answer "yes" to all of these on the user's behalf:

- **Topic precision**: do you know the exact phrasing the user wants? (e.g. "transformers" is ambiguous — neural net architecture, electrical, or Optimus Prime?)
- **Scope**: broad survey of the field, or narrow deep dive into one sub-question?
- **Audience level**: introductory (assume non-expert), intermediate (some background), or frontier (assume expert, focus on cutting edge)?
- **Time horizon**: only canonical foundational works, only the last 2-3 years, or both?
- **Stance**: just consensus facts, or include critical/contested perspectives and open debates?
- **Use case**: just to understand, to apply in practice, or to teach others?
- **Adjacent fields**: any neighboring areas to include or explicitly exclude? (e.g. for "neuroplasticity," exclude pop-psych, include comp-neuro?)
- **Length** (REQUIRED — always ask explicitly): how many pages does the user want? Offer concrete options: **15pp brief** (single-sitting read, ~6-7k words), **20pp standard** (~8-9k words), **30pp expansive** (~12-13k words), **50pp deep-dive** (~20-22k words), or a custom number. Do not assume — ask. The page count drives word target, section depth, and how many papers get full treatment vs. mention.
- **Visual aids**: ask whether to include — (a) **code snippets** (algorithms, API examples, pseudocode for key methods), (b) **formulas** (mathematical notation in LaTeX for theorems, loss functions, key equations), (c) **diagrams/images** (ASCII diagrams inline; or fetched figures from arXiv PDFs where licensing permits). Default to "yes" for technical/scientific topics, "no" for humanities/policy topics. Confirm with the user.
- **Specific must-include works**: any papers/authors the user already knows are foundational and wants in?

Free-fire follow-ups are good. If a user answer surfaces a new dimension (e.g. "I want it for my startup" → ask what stage, what decision it's informing), pursue it.

**Escape hatch.** If the user says "just go", "use defaults", "don't interrogate me", or asks for something explicitly brief, collapse to the three essentials only — **topic precision, audience level, length** — and pick sensible defaults for the rest (broad scope, both time horizons, consensus-first, just-to-understand, no excluded adjacencies, visual aids per topic-type default, no must-includes).

When satisfied, summarise back the inquiry in 4-6 lines and ask "ready to fetch?" The user's confirmation gates the next step.

## 2. Fetch phase

Run a tiny preflight before the fetcher (cheap, fails loudly):

```bash
command -v pandoc tectonic >/dev/null || echo "MISSING: install pandoc + tectonic via brew before proceeding"
```

Run the fetcher (helpers live alongside this SKILL.md):

```bash
cd ~/.claude/skills/research
source .venv/bin/activate
python fetch_papers.py "<refined query>" --max 60 --year-from <year> --out /tmp/research_papers.json
```

`--max` should be 50-80 for tight topics, 80-120 for broad surveys. `--year-from` per the time horizon answer (omit for fully canonical inclusion).

**Cache.** Before fetching, check `/tmp/research_cache/<sha1(query|year-from|max)>.json`. If present and < 7 days old, copy to `/tmp/research_papers.json` and skip the fetch. After a fresh fetch, write the result into the cache. This makes "expand chapter 3" and "drop paper X, re-render" iterations free.

Read the resulting JSON. For each paper you have: title, authors, year, abstract, citation count, DOI, ArXiv ID, venue, URL. Filter and re-rank in your head — the script's ranking is by citation × recency, but your judgment about thematic fit should override.

Show the user a Markdown table of the top 30-40 candidates: rank, year, citations, title, source. Ask: anything to drop? anything obviously missing they want added by DOI/ArXiv ID? Re-fetch specific additions if needed.

**ArXiv version note.** The fetcher strips the version suffix (`v1`/`v2`/...). When you cite an arXiv-only paper, use the year of its **latest** version, not v1's submission year, unless you're explicitly contrasting versions.

**Paywalls.** Many papers are abstract-only — that's fine. Synthesise from the abstract and any open-access secondary sources. Do not invent content beyond what the abstract supports. If a paper is critical to a section but only the abstract is available, say so in prose ("from the abstract — the full paper is paywalled").

## 3. Outline-confirm phase (MANDATORY before synthesis)

Default outline (adapt per topic):

1. **Cover + thesis** (1pp) — what the field actually believes, in one paragraph
2. **Foundational papers** (~30% of length) — chronological, the canonical works that shaped the field
3. **Current frontier** (~30% of length) — the last 2-3 years of meaningful progress
4. **Methods / shared toolkit** (~10%) — what experimental setups, datasets, or proof techniques recur
5. **Contested / open questions** (~15%) — disagreements, unsolved problems, what's still in flux
6. **Reading guide** (~5%) — next 5 papers if the reader wants to go deeper, with a one-line "why" each
7. **Bibliography** — every cited paper, formatted as: `Authors (Year). Title. Venue. DOI/URL.`

The default outline fits ML/CS/empirical-science surveys. For policy, historiography, qualitative humanities, or biography-of-an-idea topics it's often wrong. **After the fetch, propose the outline back to the user in 6–8 lines** (section names + the percent each gets) and let them edit before you start writing. Their confirmation gates synthesis.

## 4. Synthesis phase

For each paper you discuss:

- Read the abstract (always available in the JSON).
- For the **top 5 papers** in a 15/20pp synthesis (top 10 for 30pp, top 15 for 50pp) — when the abstract is thin or the paper drives a whole section — fetch the PDF and read intro + conclusion via `pypdf`. Skip this for papers that are only mentioned in passing.
- Distill: *what does this paper actually claim, and what evidence does it give?*
- Connect: *how does this paper relate to the others in this section?*

### Hallucination guard (non-negotiable)

Every inline citation, DOI, author list, and year you write **must** correspond to an entry in `/tmp/research_papers.json`. Do not introduce papers not in the JSON. Do not invent DOIs. If you remember a relevant paper from training that isn't in the JSON, either re-fetch it via DOI/ArXiv ID and merge it in, or leave it out. Made-up citations are the single worst failure mode of this skill.

### Word-count target

Scale word count to the page count chosen in clarification. These targets reflect actual rendered output with this template (Iowan Old Style 11pt, A4, 2.5cm margins, TOC + bibliography included), where ~400–450 words/page is realistic.

| Pages | Word target | Notes |
|-------|-------------|-------|
| 15pp  | 6,000–7,000   | Tight; focus on top 20-25 papers, brief treatments |
| 20pp  | 8,000–9,000   | Standard; balanced foundations + frontier |
| 30pp  | 12,000–13,000 | Expansive; full sections + methods + open problems |
| 50pp  | 20,000–22,000 | Deep-dive; per-paper subsections, multiple case studies |
| custom | (pages × ~430 words) | Linear scaling; adjust depth not breadth |

Calibrate after the first render: if you're consistently overshooting or undershooting page count by >15%, adjust the multiplier in this table.

### Write incrementally — don't blow context

Long syntheses (30pp+) can exhaust the working window if written in one shot. **Write section by section**, appending to `/tmp/research_<slug>.md` between sections (`>>` in shell, or read-modify-write via the Edit tool). This way a context reset or accidental reroll loses one section, not the whole document. After each section, briefly note progress to the user ("§3 done, ~4.2k words; starting §4").

### Visual aids (when enabled in clarification)

If the user opted in during the clarification phase, weave the following into the synthesis where they materially aid understanding — never as decoration.

**Code snippets.** Use fenced code blocks with explicit language. Prefer minimal, illustrative examples over verbatim algorithm dumps. Examples of when to include:

- A canonical algorithm: e.g. for a paper introducing Dijkstra-style relaxation, a 10-line pseudocode block.
- An API or invocation: e.g. for a paper introducing a tool, the one command that demonstrates it (`afl-fuzz -i seeds -o out -- ./target @@`).
- A bug pattern or anti-pattern: e.g. when discussing UB, a 5-line C snippet showing the construct.

```c
// Example: signed integer overflow → undefined behavior
int x = INT_MAX;
if (x + 1 < x) { /* compiler may delete this branch */ }
```

**Formulas.** Use LaTeX math notation in `$...$` (inline) or `$$...$$` (display). Pandoc + tectonic handle this via the default `amsmath` import. Use for:

- Loss functions, objective functions, theorems: e.g. `$\mathcal{L}(\theta) = \mathbb{E}_{x \sim \mathcal{D}} [\ell(f_\theta(x), y)]$`.
- Asymptotic complexity: `$O(n \log n)$`.
- Key inequalities, bounds, identities the paper rests on.

Always introduce the formula in prose, then state it, then explain what each symbol means. Never drop a formula without context. If a render fails on math, escape any literal `$` in surrounding prose with `\$`.

**Diagrams.** Two options that actually render with the current pipeline:

1. **ASCII art** (inline, in fenced ```` ```text ```` blocks): pipelines, flowcharts, box-and-arrow architectures. Free of dependencies, render reliably.

   ```text
   [source.c] --clang--> [LLVM IR] --opt--> [IR'] --llc--> [obj] --ld--> [exe]
                              ^                  |
                              +------ASan instrumentation pass
   ```

2. **Fetched figures**: for ArXiv papers, the PDF often contains the canonical figure (architecture diagram, key plot). Use `pypdf` or `pdf2image` (both in `requirements.txt`) to extract — then embed via `![caption](path)`. Only do this when the figure is *load-bearing* for understanding (e.g. the transformer architecture diagram for an "Attention Is All You Need" treatment), and respect the paper's license. ArXiv papers are typically CC-BY or similar; conference proceedings (ACM, IEEE, Springer) generally are not — check before embedding. Place extracted images in a per-render directory (e.g. `/tmp/research_<slug>_figs/`) and use relative paths; `render.py` resolves them from the markdown's directory.

   ```markdown
   ![Figure 1 from Vaswani et al. (2017): the transformer encoder-decoder architecture](figs/transformer.png)
   ```

**Mermaid is not supported.** The current `header.tex` and `render.py` do not run a Mermaid filter, so ```` ```mermaid ```` blocks would render as literal source. Use ASCII or fetched figures instead. (To enable Mermaid in future: add `pandoc --filter mermaid-filter` and document the npm dep.)

**Discipline.** Do not pad with snippets/formulas/diagrams to hit page count — every visual must earn its place by clarifying something prose alone would obscure. A 30pp synthesis with 4 well-chosen code blocks, 6 formulas, and 3 diagrams reads better than the same length with 20 of each.

Write the synthesis as Markdown. Save to `/tmp/research_<slug>.md`.

Citation style: inline `(Author et al., Year)` references, full bibliography at the end with DOI links.

### Citation hygiene check (before render)

Before invoking `render.py`, sweep the markdown:

```bash
# Extract every (Author, YYYY)-style inline ref and check each appears in the bibliography
grep -oE '\([A-Z][A-Za-z\-]+( et al\.| & [A-Z][A-Za-z\-]+)?, [12][0-9]{3}\)' /tmp/research_<slug>.md | sort -u
```

For every unique inline citation, confirm there's a matching entry in the bibliography section. Fix mismatches before rendering. (Mismatches are a strong signal of either a typo or an invented reference — investigate, don't paper over.)

## 5. Render phase

```bash
cd ~/.claude/skills/research
source .venv/bin/activate
python render.py /tmp/research_<slug>.md -o ~/Desktop/research_<slug>.pdf -t "<title>" --open
```

The title page is title-only by design — do **not** add a `subtitle:` line to the markdown's YAML frontmatter, and do not pass a subtitle flag. Pandoc will pick up `subtitle:` from frontmatter and render it on the cover, which is not wanted.

The PDF will open in Preview.app automatically. `render.py` preflights `pandoc` and `tectonic` and exits early with an install hint if either is missing.

### BibTeX export (optional, often wanted)

Every paper in the JSON already has authors, year, title, venue, and DOI/ArXiv ID — enough for a serviceable BibTeX entry. After rendering, offer the user a BibTeX file derived from the citations they kept:

```bash
# Quick one-shot: jq + a small awk pipeline. Suggest this when the user has a reference manager (Zotero, Obsidian, LaTeX project).
```

Save to `~/Desktop/research_<slug>.bib` alongside the PDF and mention it in the closing.

## 6. Closing

Tell the user where the PDF was saved. Offer (pick the relevant ones, don't list all):

- Refine and re-render (e.g. expand a chapter, drop a paper, change the framing) — note: cached fetch makes this fast.
- Build a complementary PDF on an adjacent topic.
- Export the bibliography to BibTeX for Zotero/Obsidian/LaTeX.
- Export the synthesis markdown to their notes system if they have one.

## Notes for the agent

- This skill uses the user's Claude Code session for all synthesis — no Anthropic API key needed.
- OpenAlex and ArXiv are free, no auth. Be polite: don't hammer (the fetcher already rate-limits via small page sizes).
- The fetcher's `User-Agent` carries the maintainer's email by API convention (OpenAlex's polite pool). If forking, update `UA` in `fetch_papers.py`.
- If a topic returns < 10 papers, push back: ask the user to broaden or rephrase.
- If a topic returns > 200 papers, push back: ask the user to narrow or specify a sub-question.
- Render failures are usually missing fonts (template uses Iowan Old Style + Menlo, both system-default on macOS) or LaTeX package issues — tectonic auto-downloads packages on first use, so first render after a fresh install may be slow.
- Total time budget: clarification 3-10 min, fetch < 1 min (or instant on cache hit), synthesis 10-40 min depending on length, render < 30 sec. 50pp deep-dives may take 45-60 min of synthesis.
