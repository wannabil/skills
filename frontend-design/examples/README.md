# Example — close-clone of leaf.com.my

A walkthrough of the `frontend-design` skill running in **close-clone mode**.

## The prompt

```
/frontend-design lets do leaf.com.my just copy it 100% go build dont ask me anything just go
```

## What the skill did

The user named a single reference site (`leaf.com.my`) and asked for a copy. Per § 1b of `SKILL.md`, the skill:

1. Skipped phase 2 (top-5 category research) — the reference was already chosen
2. Picked **close-clone mode** (the user did not claim ownership of the named site)
3. Screenshotted `leaf.com.my` via Playwright at desktop + mobile
4. Sampled the visual language: cyan/teal palette, light/airy header, full-bleed architectural hero with a diagonal cyan overlay, four massive single-word pillar sections on alternating cyan/white backgrounds, dark teal foundational-platform banner, solutions card grid, newsletter strip, blog cards, contact + footer
5. Built an **original** Next.js + Tailwind page in the same visual language:
   - Original brand: **ATRIUM** (smart-building operations platform)
   - Original copy throughout
   - Free Unsplash photography for the hero and section imagery
   - Montserrat (free Google Fonts grotesk) as the type
   - Same section rhythm and palette as the reference

## Result

**Above-the-fold (desktop, 1440 × 900):**

![Hero fold](./leaf-clone-fold.png)

**Above-the-fold (mobile, 390 × 844):**

![Mobile fold](./leaf-clone-mobile.png)

**Full page (desktop, scrolled):**

![Full page](./leaf-clone-full.png)

## Notes

- Screenshots in `/tmp/design-refs/<slug>/` are visual reference only — never imported into the build.
- Layout structure, color palette, and section rhythm are matched closely. Brand, copy, logos, and photographs are original / openly licensed.
- For a 1:1 rebuild (e.g. re-platforming a site you own), invoke the skill and confirm ownership when asked — it will switch to **user-owned rebuild mode** instead.
