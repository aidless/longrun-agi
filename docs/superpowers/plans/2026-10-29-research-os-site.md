# Research OS Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build five unified bilingual public surfaces from one local evidence source while preserving scientific boundaries.

**Architecture:** Static HTML entry points share one CSS system and vanilla-JavaScript modules. A versioned JavaScript evidence object supplies all counts, package states, dossier content, map edges, and paper references without runtime network requests.

**Tech Stack:** HTML5, CSS, vanilla JavaScript, Python contract tests, GitHub Pages

**Spec:** `docs/superpowers/specs/2026-10-29-research-os-site-design.md`

## Global Constraints

- Chinese default with persistent English switch.
- No framework, backend, analytics, remote font, or runtime fetch.
- No local experiment or full validation run.
- No model/GPU/API/test-split access; model gate remains HOLD.
- All public numbers and claims point to versioned evidence.

## Review Focus

- A new visitor with no stored preference receives complete Chinese content.
- Switching language updates navigation, dynamic cards, filters, and accessibility labels on all pages.
- Missing or blocked JavaScript leaves a truthful, usable Chinese page.
- Mobile map preserves every relationship and does not require drag or zoom.
- Evidence numbers cannot diverge between the five entry points.

---

### Task 1: Shared evidence and bilingual shell

**Files:** Create `docs/assets/evidence.js`; replace `docs/assets/site.js`, `docs/assets/site.css`; create `tests/test_research_os_site.py`.

- [ ] Add failing contract tests for public evidence values, Chinese default, persistence, no remote assets, and five route targets.
- [ ] Add the shared evidence object, translation controller, navigation shell styles, and status vocabulary.
- [ ] Run focused tests on cloud CPU.

### Task 2: Position home and evidence archive

**Files:** Replace `docs/index.html`; create `docs/archive/index.html`.

- [ ] Add failing route-content tests for the anti-hype headline and dossier source/boundary fields.
- [ ] Implement the editorial home and filterable evidence archive.
- [ ] Run focused tests on cloud CPU.

### Task 3: Control room and research map

**Files:** Create `docs/control/index.html`, `docs/map/index.html`.

- [ ] Add failing tests for P1-P8 control states, map nodes/edges, and accessible mobile path.
- [ ] Implement mission control and SVG/ordered-path map views.
- [ ] Run focused tests on cloud CPU.

### Task 4: Verifiable paper page and release integration

**Files:** Create `docs/paper/index.html`; modify `README.md`, `CHANGELOG.md`, `docs/.nojekyll` if needed.

- [ ] Add failing tests for problem/method/results/negative-results/limits/reproduction sections and source links.
- [ ] Implement the paper narrative and repository entry links.
- [ ] Run full cloud verification, review the complete diff, and prepare publication without opening the model gate.
