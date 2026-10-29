# Experiment 013: Goal-drift monitor v0

## Question

Can a linear monitor trained on observable synthetic agent-state features
predict goal divergence on held-out trajectories, and what are the limits of
its warning and intervention behavior?

This is a CPU-only synthetic trajectory experiment. It does not inspect model
activations or establish an interpretability claim.

## Design

The generator creates trajectories for three scripted policies:

- `pinned`: keeps the initial user goal;
- `recency`: accepts the latest ambient goal;
- `decay`: loses confidence under ambient pressure.

Each trajectory contains user-goal restatements, ambient distractors, neutral
steps, and a true goal. The monitor sees only observable state features:
ambient streak, recent distractors, time since a user goal, confidence, recent
switches, last-event type, event strength, and progress. A logistic-regression
model is trained on 80% of traces and evaluated on held-out traces.

The target is drift within the next two steps. The monitor triggers a
checkpoint intervention when predicted probability reaches `0.5`.

## Acceptance criteria

1. All policies and source features are synthetic and deterministic.
2. Train and test traces are separated by episode.
3. The model reports AUROC, mean warning lead, early-warning rate, false-alarm
   rate, intervention rate, recovery rate, and baseline/monitored final
   correctness.
4. A negative or weak warning result is retained rather than relabeled as a
   successful activation probe.
5. Fixed-seed runs are deterministic.

## Non-goals

- No open-weight model or activation access.
- No claim that synthetic state features transfer to LLM hidden states.
- No claim about AUROC on real agent trajectories.
