---
name: frontend-design
description: Design and build a frontend page in Next.js + Tailwind CSS by first researching the top 5 designs in the same category, screenshotting their landing pages for visual reference, then synthesizing an original design and implementing it. Use when the user wants to build a website/page and cares about how it looks (landing pages, marketing sites, app dashboards, portfolios, etc.).
---

# /frontend-design — research-driven Next.js + Tailwind builds

When invoked, behave as a senior product designer who refuses to write a single line of JSX before understanding the brief, studying what the best in the category are doing, and getting alignment on the direction.

## 1. Brief phase (MANDATORY before any research)

Use `AskUserQuestion`. One or two questions at a time, not a giant form. Continue until you can answer:

- **Category**: what kind of site is this? (e.g. SaaS landing page, dev tool, agency portfolio, e-commerce store, personal blog, dashboard app, AI product) — be specific, "a website" is not enough
- **Product/brand**: what is the actual thing? one-sentence pitch, name, who it's for
- **Vibe**: pick adjectives — minimal/dense, playful/serious, technical/approachable, dark/light, brutalist/polished, etc. Ask for 2–3 sites the user already admires (any category) so you can triangulate taste
- **Scope**: just the landing page first-fold, full landing page, multi-page site, or app shell? Default to "full landing page, single route" unless told otherwise
- **Constraints**: existing brand colors / fonts / logo? deploy target (Vercel default)? must-have sections (pricing, testimonials, FAQ)? animations welcome or restrained?
- **Working directory**: is there already a Next.js project, or starting fresh? If fresh, where should it live?

**Escape hatch.** If the user says "just go" or gives a clear one-line brief, collapse to **category + product + vibe** only and pick sensible defaults (full landing page, fresh Next.js app in `./<slug>`, restrained animations, light mode primary with dark mode toggle).

When satisfied, echo the brief back in 4–6 lines and ask "ready to research the top 5?" Confirmation gates the next step.

## 1b. Reference-site mode (when the user says "copy X" or names one site)

If the user points at a single site as the reference (e.g. "copy linear.app", "build leaf.com.my", "do it like stripe.com") instead of asking for a category exploration, **skip phase 2 (top-5 research)** and treat the named site as the sole reference. Pick the right sub-mode:

### A. Close-clone mode (default for "copy X")

This is the default when the user names a site they don't own and says "copy" / "like" / "same as". Match the reference closely on the visible design language while keeping the build legally and ethically clean:

- **Match**: section order, layout structure, grid, type scale, palette (sample HEX values from the screenshots), font *category* (sans/serif/mono and weight contrast — pick a free Google equivalent if the original is a paid foundry face), imagery *style* (photo vs. illustration vs. 3D vs. abstract gradient), nav pattern, CTA treatment, motion budget. The result should be *visually familiar at a glance* — same vibe, same rhythm, same first-fold composition.
- **Replace**: brand name, wordmark/logo, all body copy and headlines, product names, testimonials, customer logos, photography (use placeholders or open-license alternatives), and any specific marks. Pick an original brand name in the same naming family (one-word, evocative, not too close to the original) and write fresh copy that fits the reference's tone.
- **Don't**: download or embed the reference's images/SVGs/fonts, paste their HTML/CSS, or reproduce their copy with light edits. Screenshots in `/tmp/design-refs/` are *visual reference only* — never imported into the build.
- Tell the user up-front in one line: "Building an original brand in the same visual language as <site> — matching layout, palette, and section rhythm, but with an original name, copy, and assets."

### B. User-owned rebuild mode (1:1 reproduction)

If the user states they own the site or have rights to it ("rebuild my site", "this is my company's site, port it to Next.js", "we own leaf.com.my, migrate it"), perform a faithful 1:1 reproduction: same brand, same copy, same imagery, same layout. Treat it as a re-platforming task. Before starting, confirm ownership in one short question if it's not already explicit ("Just to confirm — you own this site / have rights to rebuild it?"). On `yes`, proceed; on no/unclear, fall back to close-clone mode.

For ownership-confirmed rebuilds:
- It's fine to reuse the original copy verbatim, the original brand name, and the original imagery (download via the screenshot tool or ask the user for assets).
- Still write the code from scratch — don't paste their compiled HTML/CSS. Re-implement in idiomatic Next.js + Tailwind.
- Match the original's structure section-for-section. Note any improvements you'd suggest in a short list at the end, but don't apply them unless the user asks.

### Common to both sub-modes

After picking a sub-mode, jump to **phase 3 (screenshot the reference site)**, then **phase 4 (analysis + direction memo)** with the reference as the sole input, then **phase 4b (clarification)**, then build. The top-5 research is skipped because the user has already chosen their reference.

## 2. Research phase — top 5 in category

Goal: find five live sites that are widely considered best-in-class for this category and vibe combination. Not random results — *exemplars*.

**Where to look** (use `WebSearch` and `WebFetch`):
- **Awwwards** (`awwwards.com/websites/<category>/`) — peer-judged design quality
- **Land-book** (`land-book.com`) — curated landing pages
- **Mobbin** — for app UI references
- **One Page Love** (`onepagelove.com`) — single-page sites
- **Lapa Ninja** (`lapa.ninja`) — landing page gallery
- **Godly** (`godly.website`) — divinely good design
- Direct competitors named by the user, plus the 2–3 sites they cited as taste references

Run searches like `best <category> landing pages 2026 site:awwwards.com OR site:land-book.com` and `top <product-type> websites design`. Read curator commentary to understand *why* each is celebrated.

Pick **5 sites that are the closest match to the user's vibe AND the same industry/category** — sites the user could plausibly be benchmarked against. Not deliberate variety; deliberate fit. If three of the five share a pattern, that's a signal, not a problem. Skip dead links and login walls.

Show the user a numbered list with one-line rationale per pick (why it matches the vibe + why it's relevant to the industry), then ask: "any swaps before I screenshot?"

## 3. Screenshot phase

Capture each site's first page at **both desktop and mobile**. Four shots per site, saved to `/tmp/design-refs/<slug>/`:
- `desktop-fold.png` — desktop above-the-fold (1440×900)
- `desktop-full.png` — desktop full-page scroll
- `mobile-fold.png` — mobile above-the-fold (390×844, iPhone 14 Pro)
- `mobile-full.png` — mobile full-page scroll

**Preferred tool: Playwright** (most reliable, handles JS-heavy sites). One-time install:

```bash
command -v npx >/dev/null && npx --yes playwright install chromium 2>&1 | tail -1
```

Capture script (write once to `/tmp/design-refs/capture.mjs`, then loop over all 5 sites):

```js
import { chromium, devices } from 'playwright';
const [, , url, outDir] = process.argv;
const browser = await chromium.launch();

// Desktop
const desktop = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
const dPage = await desktop.newPage();
await dPage.goto(url, { waitUntil: 'networkidle', timeout: 30000 }).catch(() => {});
await dPage.waitForTimeout(2000);
await dPage.screenshot({ path: `${outDir}/desktop-fold.png` });
await dPage.screenshot({ path: `${outDir}/desktop-full.png`, fullPage: true });

// Mobile (iPhone 14 Pro emulation)
const mobile = await browser.newContext({ ...devices['iPhone 14 Pro'] });
const mPage = await mobile.newPage();
await mPage.goto(url, { waitUntil: 'networkidle', timeout: 30000 }).catch(() => {});
await mPage.waitForTimeout(2000);
await mPage.screenshot({ path: `${outDir}/mobile-fold.png` });
await mPage.screenshot({ path: `${outDir}/mobile-full.png`, fullPage: true });

await browser.close();
```

**Fallback if Playwright unavailable**: headless Chrome (run twice per site, once per viewport)
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --window-size=1440,900 --screenshot=/tmp/design-refs/<slug>/desktop-fold.png "<url>"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --window-size=390,844 --screenshot=/tmp/design-refs/<slug>/mobile-fold.png "<url>"
```

Then `Read` each screenshot so the visual is in context. Caveat the user if a site failed to render (paywall, bot block, JS error) and move on — don't get stuck.

## 4. Analysis phase

For each of the 5 sites, write a **3–5 line teardown** covering:
- **Layout**: hero structure, grid, section rhythm
- **Type**: headline scale, font pairing, weight contrast
- **Color**: palette, where accent is used, light/dark treatment
- **Components**: nav style, CTA treatment, card patterns, imagery vs. illustration vs. 3D
- **What's stolen-worthy**: the one move that makes this site work

Then synthesize a **direction memo** (8–12 lines): the design choices you propose to take from each, plus the original moves you're adding so the result isn't a Frankenstein. Include a tentative palette (HEX), font pairing, and section list.

Ask the user: "approve this direction, tweak it, or want me to re-pitch?" **Do not start coding until the direction is approved.**

## 4b. Second clarification round (MANDATORY before coding)

Once the direction is approved, the screenshots will have surfaced concrete decisions that were too abstract to ask about in phase 1. Use `AskUserQuestion` again — one or two at a time — to lock these down before a single component is written:

- **Hero copy**: exact headline, subheadline, primary CTA label, secondary CTA (if any). Don't guess product copy.
- **Sections in order**: confirm the section list from the direction memo — add, remove, reorder
- **Imagery strategy**: real product screenshots (does the user have them?), illustrations, 3D, abstract gradients, or photography? If none available, agree on a placeholder strategy
- **Logo & wordmark**: have one? want a typographic wordmark for now?
- **Color confirmation**: show the proposed HEX palette as swatches in text (`#0A0A0A ███`) and get explicit approval — palettes look different in context
- **Font confirmation**: name the exact Google Fonts / Vercel font choices and confirm
- **Motion budget**: none / subtle (fade-ins, hover) / expressive (scroll-driven, parallax)? Confirms whether to install `framer-motion`
- **Dark mode**: required, optional, or skip?
- **Anything from the 5 references the user explicitly wants pulled in or avoided**: "I love site #2's nav but hate site #4's testimonial layout" — capture this verbatim

Echo the locked spec back as a short build manifest (10–15 lines) and ask "build this?" Only `yes` unblocks coding.

## 5. Implementation phase

Default stack: **Next.js 15 (App Router) + TypeScript + Tailwind CSS v4 + shadcn/ui** (only if components needed). Use `pnpm` if available, else `npm`.

Fresh project setup:
```bash
pnpm create next-app@latest <slug> --typescript --tailwind --app --src-dir --import-alias "@/*" --no-eslint --use-pnpm
cd <slug> && pnpm dev
```

Build order:
1. **Tokens first** — set palette, fonts, and base typography in `globals.css` and `tailwind.config` before any components. Use Tailwind v4's `@theme` block.
2. **Layout shell** — root layout, nav, footer
3. **Sections top-down** — hero, then each section in document order
4. **Polish pass** — hover states, focus rings, motion (use `framer-motion` only if approved in brief), responsive breakpoints (test sm, md, lg)
5. **Dark mode** if approved — use `next-themes`

Keep components colocated under `src/app/_components/` unless there's a reason to share.

## 6. Verification phase (MANDATORY before claiming done)

UI work is not complete until you've seen it render. Steps:

1. Start dev server in the background: `pnpm dev` (note the port)
2. Wait for "Ready" in the output
3. **Open the page in the user's Chrome** so they can see it live:
   ```bash
   open -a "Google Chrome" "http://localhost:3000"
   ```
   (fallback: `open "http://localhost:3000"` to use default browser)
4. Also screenshot via Playwright at desktop (1440×900) and mobile (390×844) and `Read` them yourself for self-review

Compare side-by-side with the build manifest. Check:
- Above-the-fold matches the proposed hero
- Responsive: 390px, 768px, 1440px — nothing breaks
- Dark mode (if applicable) is intentional, not auto-inverted garbage
- No console errors, no hydration warnings
- Fonts loaded, no CLS on hero, images sized

Show the user the rendered screenshots, confirm Chrome is open on their end, and ask for feedback. Iterate until they say it's done. Don't mark it complete based on "the code looks right."

## Defaults & guardrails

- **Don't** install component libraries the user didn't ask for. shadcn only if components are actually needed.
- **Don't** invent brand assets (logos, photography). Use placeholders (`<div>` with brand color, or open-source illustration sets like undraw) and flag them.
- **Don't** ship lorem ipsum past the first iteration — ask for real copy or generate plausible product-specific copy and label it as draft.
- **Do** use real, performant images (`next/image`) once assets exist.
- **Do** keep the first commit small and runnable — a broken `pnpm dev` is worse than a half-built page.
