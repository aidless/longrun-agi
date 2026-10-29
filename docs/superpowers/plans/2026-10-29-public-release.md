# Public Release and Evidence Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a verifiable v0.1.0 public release, evidence dashboard, and open-source governance surface without opening the model gate.

**Architecture:** A dependency-free static site in `docs/` links to immutable repository evidence. GitHub Actions verifies Python evidence and deploys Pages separately; community files and model application forms live in version control.

**Tech Stack:** HTML5, CSS, vanilla JavaScript, Python 3.11+, GitHub Actions, GitHub CLI

**Spec:** `docs/superpowers/specs/2026-10-29-public-release-design.md`

## Global Constraints

- No local experiment or full validation run.
- No model/GPU/API/test-split access.
- Keep model gate `HOLD` and avoid model-capability or production claims.
- Public identity is `LongRun-AGI` by `aidless`.

## Review Focus

- Dashboard numbers must match versioned evidence and link to their sources.
- Mobile and reduced-motion users must retain access to every section.
- GitHub Pages must not require a package install or build service.
- Security reporting must not promise unsupported private channels.
- Release must point to the exact commit that passed public CI.

---

### Task 1: Static evidence dashboard

**Files:** Create `docs/index.html`, `docs/assets/site.css`, `docs/assets/site.js`, `tests/test_public_site.py`; modify `README.md`.

- [ ] Write tests asserting required evidence labels, source links, accessibility landmarks, and absence of unsupported claims.
- [ ] Run the focused test remotely and confirm it fails because the site is absent.
- [ ] Implement the dependency-free responsive site and link it from README.
- [ ] Run focused tests remotely and confirm they pass.

### Task 2: Open-source governance and model application

**Files:** Create `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `ROADMAP.md`, `.github/ISSUE_TEMPLATE/*`, `.github/pull_request_template.md`, `.github/CODEOWNERS`, `MODEL-GATE-APPLICATION.md`; modify `MODEL-GATE.md` and `README.md`.

- [ ] Add static contract tests for required boundaries and workflow fields.
- [ ] Confirm tests fail before adding the files.
- [ ] Add concise governance documents and forms.
- [ ] Confirm focused tests pass remotely.

### Task 3: Pages deployment and CI modernization

**Files:** Create `.github/workflows/pages.yml`; modify `.github/workflows/ci.yml`.

- [ ] Add contract tests for deployment permissions, concurrency, and no package/build step.
- [ ] Confirm tests fail before workflow creation.
- [ ] Add Pages deployment and update first-party Actions to Node 24-compatible major versions.
- [ ] Confirm focused tests pass remotely.

### Task 4: Full verification and publication

**Files:** Modify only generated audit artifacts if the repository's established audit process requires a new sealed version.

- [ ] Run pytest, compileall, portfolio audit check, and make verify on `ecs-hz`.
- [ ] Commit and push the reviewed changes.
- [ ] Wait for public CI and Pages deployment.
- [ ] Enable Pages, configure branch protection if supported, open roadmap issues, and publish release `v0.1.0` at the verified commit.
- [ ] Verify repository visibility, release/tag target, issue URLs, Pages response, and branch settings.
