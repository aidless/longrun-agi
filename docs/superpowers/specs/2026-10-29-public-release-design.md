# Public Release and Evidence Site Design

**Date:** 2026-10-29

## Intent

Turn the verified LongRun-AGI repository into a stable, understandable public release for researchers and engineering evaluators. The public surface must make evidence and limitations equally prominent.

## Goals

- Publish an immutable `v0.1.0` release from a freshly verified commit.
- Provide a dependency-free GitHub Pages evidence dashboard for P1-P8.
- Add standard contribution, security, issue, and pull-request workflows.
- Record a public roadmap and actionable issues.
- Add a model-gate application template without opening the gate.
- Require CI on changes to `main` where GitHub plan capabilities permit.

## Non-goals

- No model download, inference, training, GPU use, paid API call, or test-split access.
- No external benchmark, novelty, capability, production-readiness, or AGI claim.
- No JavaScript framework, analytics, cookies, server, database, or dynamic backend.

## Approach

Use a hand-authored static site in `docs/` with semantic HTML, CSS, and a small progressive-enhancement script. The page links directly to versioned repository evidence and exposes the exact verification counts and model HOLD boundary. GitHub Pages deploys the checked-in site through an Actions workflow. This is preferred over Jekyll or a frontend framework because it adds no dependency chain and keeps the public representation auditable.

## Public identity

Use project name `LongRun-AGI`; display author identity only as GitHub account `aidless`.

## Verification and release

Cloud `ecs-hz` remains the execution environment for the complete test, compile, portfolio, and artifact checks. Local work is limited to editing and short static checks. Release creation and GitHub settings occur only after the cloud verification and public CI pass.

## Safety

The dashboard must label scripted and synthetic evidence explicitly. Model status remains `HOLD`. Branch protection must not bypass administrators silently; if the repository plan does not support rulesets, record that limitation rather than claiming protection.
