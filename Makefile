PYTHON ?= python3
export PYTHONPATH := src

.PHONY: test clear faults memory controls confounding-control claim-schema factorial three-factor estimator-validity clear-v1 clear-v1-verify layered-memory persistent-memory recovery-matrix real-faults research-agent goal-drift-monitor world-model-calibration model-protocol verifier-rewards adaptive-controller program-quick program portfolio-audit verify

test:
	$(PYTHON) -m pytest

clear:
	$(PYTHON) -m longrun.cli clear-eval --instances 4 \
		--output experiments/000-clear-v0/results/clear-eval.json

faults:
	$(PYTHON) -m longrun.cli clear-faults \
		--output experiments/000-clear-v0/results/clear-faults.json

memory:
	$(PYTHON) -m longrun.cli provmem-audit --scenarios 24 \
		--output experiments/000-clear-v0/results/provmem-audit.json

controls:
	$(PYTHON) -m longrun.cli controls-audit \
		--output experiments/000-clear-v0/results/controls-audit.json

factorial:
	$(PYTHON) -m longrun.cli factorial-eval --instances 4 \
		--output experiments/001-factorial-v0/results/factorial-eval.json

three-factor:
	$(PYTHON) -m longrun.cli three-factor-eval --instances 4 \
		--output experiments/002-three-factor-v0/results/three-factor-eval.json

estimator-validity:
	$(PYTHON) -m longrun.cli estimator-validity \
		--repetitions 200 \
		--bootstrap-replicates 299 \
		--seed 20261027 \
		--output experiments/003-estimator-validity-v0/results/estimator-grid.json

clear-v1:
	$(PYTHON) scripts/freeze_clear_v1.py \
		--output-dir benchmarks/clear-300-v1 --seed 20261028

clear-v1-verify:
	$(PYTHON) scripts/verify_clear_v1.py benchmarks/clear-300-v1

layered-memory:
	$(PYTHON) -m longrun.cli layered-memory --episodes 100 \
		--seed 20261028 \
		--output experiments/010-layered-memory-v0/results/layered-memory.json

persistent-memory:
	$(PYTHON) -m longrun.cli persistent-memory --episodes 32 \
		--output experiments/019-persistent-memory-v0/results/persistent-memory.json

recovery-matrix:
	$(PYTHON) -m longrun.cli recovery-matrix \
		--output experiments/011-recovery-v0/results/recovery-matrix.json

real-faults:
	$(PYTHON) -m longrun.cli real-faults \
		--output experiments/021-real-faults-v0/results/real-faults.json

research-agent:
	$(PYTHON) -m longrun.cli research-agent \
		--output experiments/012-negative-control-agent-v0/results/research-agent.json

confounding-control:
	$(PYTHON) -m longrun.cli confounding-control \
		--output experiments/017-confounding-control-v0/results/confounding-control.json

claim-schema:
	$(PYTHON) -m longrun.cli claim-schema \
		--output experiments/018-claim-schema-v0/results/claim-schema.json

goal-drift-monitor:
	$(PYTHON) -m longrun.cli goal-drift-monitor --episodes 60 --steps 40 \
		--seed 20261028 \
		--output experiments/013-goal-drift-monitor-v0/results/monitor.json

world-model-calibration:
	$(PYTHON) -m longrun.cli world-model-calibration --samples 20 \
		--seed 20261028 \
		--output experiments/014-world-model-calibration-v0/results/calibration.json

verifier-rewards:
	$(PYTHON) -m longrun.cli verifier-rewards --train-episodes 600 \
		--seed 20261028 \
		--output experiments/015-verifier-rewards-v0/results/rewards.json

adaptive-controller:
	$(PYTHON) -m longrun.cli adaptive-controller --train-episodes 600 \
		--seed 20261028 \
		--output experiments/016-adaptive-controller-v0/results/controller.json

model-protocol:
	$(PYTHON) -m longrun.cli model-protocol \
		--output experiments/020-model-protocol-v0/results/model-protocol.json

program-quick:
	$(PYTHON) -m longrun.cli program --quick \
		--output experiments/008-cpu-program-v0/results/quick.json

program:
	$(PYTHON) -m longrun.cli program \
		--output experiments/008-cpu-program-v0/results/program.json

portfolio-audit:
	$(PYTHON) scripts/audit_portfolio.py

verify:
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-bootstrap-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/factorial-attribution-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/factorial-attribution-v0/v2
	$(PYTHON) scripts/verify_artifact.py artifacts/three-factor-attribution-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/estimator-validity-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/clear-300-v1/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/layered-memory-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/layered-memory-v0/v2
	$(PYTHON) scripts/verify_artifact.py artifacts/layered-memory-v0/v3
	$(PYTHON) scripts/verify_artifact.py artifacts/recovery-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/recovery-v0/v2
	$(PYTHON) scripts/verify_artifact.py artifacts/negative-control-agent-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/goal-drift-monitor-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/world-model-calibration-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/verifier-rewards-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/verifier-rewards-v0/v2
	$(PYTHON) scripts/verify_artifact.py artifacts/adaptive-controller-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v2
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v3
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v4
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v5
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v6
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v7
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v8
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v9
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v10
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v11
	$(PYTHON) scripts/verify_artifact.py artifacts/cpu-program-v0/v12
	$(PYTHON) scripts/verify_artifact.py artifacts/confounding-control-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/claim-schema-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/persistent-memory-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/model-protocol-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/real-faults-v0/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/portfolio-v1/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/portfolio-v2/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/portfolio-v3/v1
	$(PYTHON) scripts/verify_artifact.py artifacts/portfolio-v4/v1
