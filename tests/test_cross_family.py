from longrun.clear.cross_family import run_cross_family_probe


def test_cross_family_transfer_is_explicitly_measured():
    result = run_cross_family_probe(seed=31)
    assert set(result["directions"]) == {
        "extension_to_prefix",
        "prefix_to_suffix",
        "suffix_to_extension",
    }
    for row in result["directions"].values():
        assert row["train_success"] == 1.0
        assert row["transfer_success"] == 0.0
        assert row["transfer_drop"] == 1.0


def test_cross_family_probe_is_deterministic():
    assert run_cross_family_probe(seed=31) == run_cross_family_probe(seed=31)


def test_cross_family_policy_is_reused_instead_of_recreated():
    result = run_cross_family_probe(seed=31)
    assert result["execution"]["policy_reused"] is True
    assert result["execution"]["source_episodes_before_transfer"] == 2
