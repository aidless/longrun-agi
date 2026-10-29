# Experiment 020 Log

## 2026-10-29: Cloud CPU dry run

The frozen CLEAR-300-v1 model protocol completed a 240-task train/dev fixture
dry run on `ecs-hz`. The valid fixture scored `240/240`; the mixed fixture
scored `203/240` with injected timeout, invalid JSON, and wrong-output cases.
The 60-task test split remained sealed.

Protocol SHA-256:
`1916f54b2d1a870c850bb2be7f7badae1f1e4193849635497c5f83297cd76655`

Raw output SHA-256:
`94220f8c4f073e32e0d65ee6338da6eb66df91e70f357391fc5d3a877dfdba66`

Canonical output SHA-256:
`bed43ac805ec30f43589c9e5f7a0fcb5f032a08f84fbc6303a887a09743b93dd`

No model was downloaded or loaded and no model capability result is claimed.
