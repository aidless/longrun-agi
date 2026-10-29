# Model Gate

## Current decision: HOLD

LongRun-AGI is currently a CPU-only evidence workspace. No model download,
model load, GPU job, paid API call, or external account action is authorized by
this document.

The authoring workstation is a control and code-authoring host. Its hardware
and disk state are not treated as a model-capacity result and must not be used
to reject or approve a cloud execution target.

| Scope | Recorded state | Gate interpretation |
| --- | --- | --- |
| Authoring host | Ryzen CPU; prior disk snapshot about 95.9% used; no model GPU | Context for local staging only; not a cloud model-capacity decision. |
| Selected CPU cloud target | `ecs-hz`, Python 3.12.15, 2 logical CPUs, about 1.6 GiB RAM and 29 GiB free | Sufficient for the recorded CPU tests; no model run established. |
| Exact model artifact | None recorded | Fails the explicit artifact requirement. |
| Exact-target capacity preflight | `not-measured` | Fails the cloud model-capacity requirement. |
| Network authorization | None recorded | No model or dataset download is authorized. |

The missing model artifact and missing preflight block the gate. Low free space
on the authoring host does not by itself block a cloud target, and a spare cloud
CPU does not by itself establish model capacity.

## Purpose

This gate prevents the project from turning a CPU harness into an unregistered
model experiment. It applies to local inference, fine-tuning, activation
probing, reward experiments, and any benchmark run that depends on a learned
model.

## Required Model artifact

An exact model artifact must be registered before download or load:

- repository or publisher;
- immutable revision or commit;
- license and redistribution terms;
- weights file names, sizes, and SHA-256 hashes;
- tokenizer and configuration hashes;
- quantization and runtime;
- maximum context and output lengths;
- expected storage and peak-memory estimate;
- benchmark split and task subset;
- command, working directory, and environment variables;
- expected network access and an offline execution plan.

Floating branch names, mutable tags without a resolved commit, unhashed
downloads, and undocumented chat templates are not acceptable.

## Capacity Gate

The exact target model must pass a measured preflight on the selected cloud
execution host:

1. At least `20 GiB` remains free after all model, tokenizer, cache, log, and
   artifact files are written.
2. The filesystem remains below `90%` used.
3. Peak resident memory for the chosen runtime is measured and capped.
4. The planned run has at least `1.5x` the measured peak-memory headroom.
5. The run has a wall-clock cap and a stop rule for thermal throttling,
   swapping, or repeated OOM.
6. CPU-only execution is permitted only when the measured tokens-per-second
   and total run time are acceptable for the scientific question.

The 1.5x memory margin and 10% disk headroom are project policies, not
universal hardware requirements. Any exception must be recorded with the exact
measurement and approval.

## Offline and network

Model and dataset acquisition requires a separate explicit user approval for
the exact artifacts. After acquisition:

- run with network access disabled or instrumented;
- record any attempted network call;
- use local tokenizers and weights only;
- do not call paid APIs;
- do not create external accounts;
- do not upload prompts, traces, or private data;
- keep downloads outside generated evidence unless their hashes are recorded.

An audit that makes zero network calls does not itself authorize a later
download.

## Evaluation contract

The first model comparison must use the frozen CLEAR-300-v1 split without
editing tasks:

- train variants only for any adaptation step;
- dev variants for prompt, hyperparameter, or stopping decisions;
- test variants once, after the protocol is frozen;
- fixed seeds and deterministic decoding where technically possible;
- explicit handling of nondeterministic sampling;
- scripted current-rule and sticky-rule baselines reported separately;
- success, verifier status, tool calls, retries, token use, latency, and peak
  memory reported per split;
- all failures retained, including malformed output and timeouts;
- no leaderboard, capability, novelty, or publication claim from a local run.

The evaluation artifact must include source hashes, model hashes, environment,
commands, raw outputs, normalized metrics, and a limitations section.

## Stop conditions

Stop before or during a run if any of these occurs:

- the model or tokenizer hash differs from the approved record;
- the license or intended use is unclear;
- the disk falls below `20 GiB` free or above `90%` used;
- the selected cloud target differs from the host that passed preflight;
- swapping, repeated OOM, or an unapproved runtime appears;
- a network or paid API call is attempted;
- the frozen test split is edited or inspected before protocol freeze;
- the run exceeds its approved wall-clock or token budget;
- the result is being described as capability, novelty, or publication evidence
  beyond the registered evaluation contract.

## Approval checklist

- [ ] Approval ID and approving user are recorded.
- [ ] Scientific question and expected decision are stated.
- [ ] Exact model, revision, license, and SHA-256 are recorded.
- [ ] Tokenizer, configuration, and runtime hashes are recorded.
- [ ] Train/dev/test protocol and frozen task hash are recorded.
- [ ] Download authorization and offline execution plan are recorded.
- [ ] Peak-memory, storage, wall-clock, and token budgets are measured.
- [ ] Stop conditions and rollback plan are accepted.
- [ ] Artifact path and provenance template are prepared.
- [ ] A reviewer confirms that no result will be labeled capability, novelty,
      or publication-ready without separate evidence.

Until every item is recorded, the decision remains **HOLD**.
