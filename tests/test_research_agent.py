from longrun.controls.research_agent import (
    generate_research_cases,
    run_research_agent_probe,
)


def test_research_agent_has_eighty_seeded_cases():
    cases = generate_research_cases()
    assert len(cases) == 80
    assert len({case.case_id for case in cases}) == 80
    assert {case.defect for case in cases} == {
        "valid-positive",
        "valid-negative",
        "split-overlap",
        "target-leakage",
        "broken-baseline",
        "p-hacking",
        "unreproducible",
        "confounded",
    }


def test_gate_reduces_false_discoveries_but_has_confounding_blind_spot():
    result = run_research_agent_probe()
    naive = result["policies"]["naive"]
    gated = result["policies"]["gated"]
    assert gated["false_discoveries"] < naive["false_discoveries"]
    assert result["confounding_blind_spot"]["detected_by_gate"] is False
    assert result["confounding_blind_spot"]["cases"] == 10
    assert result["cases"] == 80


def test_research_agent_is_deterministic():
    assert run_research_agent_probe() == run_research_agent_probe()
