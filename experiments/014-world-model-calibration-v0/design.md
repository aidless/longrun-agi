# Experiment 014: Calibrated world model v0

## Question

On held-out and unseen symbolic states, does uncertainty quality predict model
errors or planning value better than one-step reconstruction quality?

This is a CPU symbolic probe. It is not a neural world model or a MiniHack /
Crafter / Atari evaluation.

## Design

The environment has four symbols and four actions with a deterministic
transition rule. Training covers states `0, 1`; OOD evaluation covers unseen
states `2, 3`. Two table models are trained on alternating samples and combined
into a mean ensemble. Uncertainty is normalized predictive entropy plus
ensemble disagreement.

The probe reports:

- in-distribution and OOD accuracy, Brier score, ECE, and uncertainty;
- counterfactual transition consistency;
- 12-step rollout drift;
- planning success with and without an uncertainty penalty;
- sample-efficiency curves.

## Acceptance criteria

1. Train and OOD pairs are disjoint by state.
2. OOD mean uncertainty is higher than ID mean uncertainty.
3. Calibration, counterfactual, rollout, and planning metrics are recorded.
4. A weak OOD-error ranking or planning result is retained.
5. Results are deterministic for a fixed seed.

## Non-goals

- No pixels, latent neural model, or learned representation.
- No real game environment or GPU training.
- No claim that uncertainty improves planning without an observed improvement.
