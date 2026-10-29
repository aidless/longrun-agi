# LongRun-AGI Research OS Site Design

**Date:** 2026-10-29

## Intent

Replace the single evidence page with one memorable bilingual research operating system. It serves five reader needs without becoming five unrelated websites: public position, evidence inspection, operational status, system understanding, and academic citation.

## Information architecture

- `/`: a confrontational position page led by “我们没有证明 AGI。”
- `/archive/`: evidence dossiers with source links, outcomes, limits, and hashes.
- `/control/`: a high-density P1-P8 mission-control view.
- `/map/`: an interactive relationship map with an accessible mobile path.
- `/paper/`: a verifiable paper-style narrative from question through limitations and reproduction.

All pages share navigation, bilingual copy, a versioned evidence data file, and the same status vocabulary.

## Visual system

Use an ivory archive-paper field, carbon-black structure, warning red for blocked/unsupported claims, and verification green for recorded checks. Typography uses local expressive serif and mono fallbacks, with oversized editorial headlines, dossier stamps, graph lines, and restrained scan/reveal motion. Avoid SaaS cards, neon hacker imagery, and framework-default layouts.

## Language behavior

Chinese is the initial default. A visible `English` control switches every supported text node and persists `en` or `zh` in `localStorage`. The page remains complete and readable with JavaScript disabled in Chinese. Navigation, filters, statuses, evidence limits, and accessibility labels are bilingual.

## Evidence architecture

`/assets/evidence.js` is the single versioned public data source. It records release metadata, verification counts, scientific boundaries, P1-P8 package status, archive dossiers, map edges, and reproduction commands. It must not fetch network data at runtime. Every quantitative claim links to an existing versioned repository artifact or status file.

## Interaction and accessibility

- Keyboard-operable language switch, filters, dossier disclosures, and map node selection.
- Semantic landmarks, visible focus, skip links, and reduced-motion support.
- Desktop map uses SVG connections; mobile presents the same relationships as an ordered path.
- Filters and language are progressive enhancement; evidence stays in the HTML or generated locally from embedded data.

## Boundaries

Model gate stays `HOLD`. The site must say that no model evaluation, GPU job, paid API call, external benchmark result, novelty finding, production-readiness finding, or AGI result exists. No analytics, cookies, backend, package manager, remote font, or frontend framework is permitted.
