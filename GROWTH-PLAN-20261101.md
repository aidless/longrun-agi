# Growth Plan: 2026-11-01

Written after the second literature pass (`literature/search_20261101.md`,
59 new candidates in `literature/candidates_20261101.json`).

The instruction that produced this file: **make the project bigger before making
it smaller.** This document says what "bigger" means concretely, what it costs,
and what would make us abandon each addition. It is a plan, not a result. Nothing
below is registered as an experiment until its probe is written.

## 1. What is actually missing

The central question is:

> Can a single agent remain reliable and adaptive **over a long series of tasks**
> when rules change, tools fail, memory is stale or poisoned, and evidence must
> be audited?

Every stress factor in that sentence is covered by a work package. The one thing
that is **not** covered is the phrase *over a long series of tasks*. CLEAR-300-v1
is 300 **independent** draws: each task starts clean, and the score is a per-task
mean. Nothing in the portfolio measures a sequence. So today the project can
answer "does the agent handle a hard task?" but not "does it still work on
session 40?"

Three structural consequences, in order of severity:

**Gap A — no series axis.** No carryover state between sessions, no decay curve,
no onset point, no variance-vs-mean separation. The literature has moved to
exactly this (`2603.29231` reliability decay / graceful degradation / meltdown
onset; `openreview-tapestry` argues benchmarks *isolate episodes* and proposes
continuous streams; `openreview-web2longtraj` supplies operators that manufacture
cross-session dependency).

**Gap B — no metric-validity axis.** 190 tests over 33 files prove the harness is
deterministic. That is a statement about the *machine*, not about the *scores*.
`emnlp-2026-industry-25` calibrates metrics by perturbing 4,973 golden workflows;
`arxiv-2608.06940` shows an aggregate metric can be valid in the mean and blind
exactly where the effect concentrates; `rs-11407058` documents 22 agent-built
benchmarks that were green and approved, where probing still found defects in all
22 and at least 13 recorded a strategy that ignored the task and still earned
credit.

**Gap C — three "weak/negative" probes are weak for structural reasons, not
measurement noise.** Read against the new literature, each has a named cause:

| Package | Current reading | Structural cause visible in the literature |
| --- | --- | --- |
| P4 World Model | ID `1.0`, OOD `0.25`, OOD error AUROC `0.5`, planning `0.5` = argmax | A symbolic lag model has no error model to compound; `dai-s44163` frames world-model failure as *compounding error plus planner exploitation*, neither of which a lag model can express |
| P6 Goal Drift | held-out AUROC `0.8295`, early-warning rate `0.0`, monitored correctness `0.5556` = baseline | The monitor has no goal-consistent reference trajectory to measure against; `arxiv-2510.07777` defines drift as divergence *from a reference model* and gets a usable signal only then |
| P8 Compute Controller | value-density `807`/`88` misses; safe variant `530`/`0`; adaptive `0.4833` with `0` memory writes | The controller has no cost signal that distinguishes arms; `arxiv-2606.25115` prices memory by *net value per byte* under an explicit budget |

These are the honest entries into "bigger". They are not "run it again louder".

## 2. Four additions (P9–P12)

Each is scoped to the CPU substrate that already exists, following the project's
own rule that a probe demonstrating a *harness* property is not a claim about
model capability. Every one of them has a falsifier written before the probe.

### P9 — Reliability Decay and Meltdown Onset

**Question.** On a *dependent* stream of sessions, does success degrade gradually,
or hold and then fall off a cliff — and which signal moves first?

**Why now.** This is the only gap that touches the central question directly.
`arxiv-2603.29231` gives the vocabulary (decay curve, variance amplification,
graceful-degradation score, meltdown onset) and the external anchor; `LADDER`
reports the same shape outside our domain (85.4% on single-subgoal tasks falling
to near zero as subgoals extend), which matters because it means the drop is
expected, not a bug in our substrate.

**Minimal probe.** `CLEAR-300-L`: keep the 300 frozen tasks byte-identical, add a
serial wrapper that (i) carries residual state forward — leftover files, stale
memory entries, a rule sheet from the previous session, (ii) runs `K = 10`
sessions per stream, (iii) records per-session pass rate, per-session variance,
and first-session-at-or-below-threshold. Score with three scripted policies
(current-rule, sticky-first-rule, no-memory) so the reading is a harness contrast
and stays comparable to the existing `1.0` vs `0.3133` baseline.

**Falsifier.** If pass rate across session index is flat within the deterministic
noise band, then carryover does not bind in this substrate and P9 reports a
negative result with an explicit statement of what would be needed to make it
bind (real tool state, or genuine model non-determinism).

**Cost.** CPU only. Substrate exists; the work is the wrapper, the residual-state
schema, and 3 × 10 × 300 deterministic episodes.

**Done when.** A decay curve exists with a stated threshold, an onset point per
policy, and a variance series alongside the mean series.

### P10 — Self-Evolution Erosion

**Question.** Does the reusable state the harness accumulates (rules, skills,
memory) *cost* capability on tasks it previously passed?

**Why now.** The project assumes accumulation is free. `arxiv-2610.25858` finds
self-evolving harnesses are **not** effective continual learners on drifting
streams; `arxiv-2605.09315` names capability erosion across workflow / skill /
model / memory channels; `arxiv-2610.11373` reports catastrophic forgetting from
prompt optimization. P7's sticky-first-rule result (`0.3133` against `1.0` for
current-rule) is already a *hint* of this mechanism, currently filed as a harness
contrast rather than as erosion.

**Minimal probe.** Freeze a passing task set, let a scripted "evolution" pass add
rules/skills according to four accumulation policies (append-only, per-channel,
budget-capped, evict-by-use), then re-run the *frozen* set. Erosion = post-minus-pre
pass rate on tasks that passed pre-evolution, reported per policy and per channel.

**Falsifier.** If every accumulation policy leaves the frozen set at its pre
level, accumulation is free here and the erosion claim is rejected for this
substrate.

**Cost.** CPU only, the cheapest of the four — the frozen set already exists.

**Done when.** A per-channel erosion table exists with confidence intervals, and
the sticky-first-rule result is either explained by it or explicitly left
unexplained.

### P11 — Memory Lifecycle: Sleeper, Laundering, Deletion

**Question.** Does provenance surviving *injection time* imply it survives
*consolidation*, *delay*, and *deletion*?

**Why now.** P3/ProvMem measures poison at injection and gets a clean contrast
(flat `1.0` to layered `0.0`). That result is silent about three attacks the
literature now treats as separate: delayed/dormant triggers (`arxiv-2605.15338`),
provenance stripped by consolidation (`arxiv-2607.29167`), and behavioural
residuals of deletion (`ssrn-7428966`, which challenges the active-forgetting
assumption outright). `ssrn-7480138` supplies the cascading-invalidation design.

**Minimal probe.** Three arms on the existing ProvMem substrate: (i) poison that
fires only after `N` sessions, (ii) poison whose provenance label is rewritten by
a consolidation step before use, (iii) a memory marked deleted but still readable
by the retrieval path. Each arm reports whether the layered policy still wins.

**Falsifier.** If layered provenance holds in all three arms, the lifecycle
extension is unnecessary and P3's claim is stronger than we thought — which is a
result worth having.

**Cost.** CPU only. Substrate exists; new work is the consolidation step.

**Done when.** All three arms report, and P3's published claim has an explicit
scope boundary ("injection-time provenance, not consolidation-stable
provenance") either added or refuted.

### P12 — Metric Validity Battery

**Question.** For each metric the portfolio reports, does it move when the
failure moves — and where is it blind?

**Why now.** This is the package that protects the other eleven. Without it, a
decay curve (P9) could be measuring scheduler drift; a provenance win (P3/P11)
could be measuring task difficulty; and a green test suite says nothing, as
`rs-11407058` documents for 22 benchmarks that were exactly in our position.
`emnlp-2026-industry-25` gives the method (graded perturbations of golden
artifacts, then check the metric responds monotonically); `arxiv-2603.29665`
supplies the *near-miss* axis (right outcome via a skipped check) that our
evidence gate cannot currently see; `arxiv-2608.06940` supplies the blindness
test (does the aggregate metric detect the change that concentrates in a
one-vote-margin subset?).

**Minimal probe.** (i) Build a perturbation ladder over the seven deterministic
evidence-gate controls and assert monotone response; (ii) inject near-misses
(outcome correct, required check skipped) and confirm at least one metric flags
them; (iii) split each existing headline reading into "where the effect
concentrates" versus "aggregate" and report both.

**Falsifier.** If a metric fails monotonicity, that is a defect in the metric, and
every prior number produced by it gets an annotation until it is fixed. This
package is allowed to *retract* earlier readings.

**Cost.** CPU only, no new data.

**Done when.** A validity table exists per metric with `PASS` / `BLIND_SPOT` /
`FAILS_MONOTONICITY`, and P12 runs in CI so it cannot silently rot.

## 3. Hypotheses to register (H16–H20)

Wording is falsifiable on the CPU substrate; each maps to one package.

- **H16 (P9).** In a serial-carryover CLEAR split, per-session pass rate declines
  monotonically in session index for at least one scripted policy, and the
  first-session-at-or-below-threshold onset occurs strictly before the mean
  decline exceeds the deterministic noise band.
- **H17 (P9).** Per-session variance amplification grows with session index
  faster than the mean declines, so variance is an earlier warning signal than
  the mean.
- **H18 (P10).** Accumulated reusable state produces measurable erosion on a
  previously-passing frozen task set, and the erosion is larger for procedural
  state than for episodic state.
- **H19 (P11).** Deleted memory leaves a behavioural residual detectable in
  tool-choice distributions, even when the reported context no longer contains it.
- **H20 (P12).** At least one headline metric in the portfolio is blind to a
  failure class that another metric detects; therefore no single metric is
  sufficient to support the portfolio's claims.

## 4. `CLEAR-300-L` design sketch

Constraints that make this buildable in a day rather than a month:

1. **Do not modify CLEAR-300-v1.** The frozen artifact stays byte-identical;
   `CLEAR-300-L` is a *wrapper artifact* that references it by hash. Changing the
   frozen set in place would invalidate every prior reading (`PORTFOLIO-STATUS.md`
   already flags this as evaluation drift).
2. **Streams, not new tasks.** A stream is `K = 10` sessions drawn from the
   existing 300 with a deterministic seed. No new task authoring.
3. **Residual state is explicit and inspectable.** Carry only three things —
   leftover files in the sandbox, memory entries, and the rule sheet — and dump
   them per session so a decay curve can be attributed to a specific channel.
4. **Scripted policies first.** Three policies, deterministic, so P9's first
   reading is a harness contrast like P7's `1.0` vs `0.3133`. Model evaluation
   stays behind `MODEL-GATE.md`.
5. **The split stays sealed.** `180/60/60` is preserved; the test split remains
   unread until a separate go/no-go.

## 5. Sequencing

```
P12 (metric validity)  ──►  gate for everything below
        │
        ├──► P9  (series axis)  ──► H16, H17
        │            │
        │            └──► P10 (erosion on the frozen set produced by P9)
        │
        └──► P11 (memory lifecycle) ──► H19, and re-scopes P3's claim
```

Rationale: P12 first because it can retract other readings, and it is cheapest.
P9 second because it produces the frozen "previously passed" set that P10 needs.
P11 is independent and can run in parallel with P9.

## 6. What not to do

- **No GPU, no API spend, no model download** in this plan. `MODEL-GATE.md` is
  untouched. Every item above is a harness property measured on the deterministic
  substrate, and must be described that way in any write-up.
- **No new task authoring** beyond what P9's stream wrapper requires.
- **No replacement of failed probes with stronger prose** (`ROADMAP.md` stop
  rule). P4 and P6 stay labelled weak/negative until a probe actually moves them.
- **No retro-fitting.** If P12 finds a metric fails monotonicity, earlier numbers
  get annotated; they do not get quietly re-derived to look better.

## 7. Cost and done-criteria

| Item | Compute | New code | Can retract prior results |
| --- | --- | --- | --- |
| P12 metric validity | CPU, minutes | perturbation ladder + near-miss injector | **yes** |
| P9 reliability decay | CPU, hours | stream wrapper + residual-state schema | no |
| P10 erosion | CPU, minutes | 4 accumulation policies | no |
| P11 memory lifecycle | CPU, hours | consolidation step + 3 arms | re-scopes P3 |

## 8. Stop rules

- If P12 shows the headline metrics fail monotonicity, **stop adding packages**
  and fix the metrics first.
- If P9's decay is flat, do not shop for a substrate that produces decay; report
  the negative result and say what would be required.
- If P10's erosion is zero under every policy, drop the self-evolution dimension
  rather than keep it as narrative.
- Any item that cannot be finished inside one CPU probe session gets split, not
  extended.
