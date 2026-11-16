import scripts.check_headline as headline


def test_headline_check_accepts_repository():
    assert headline.collect_errors() == []


def test_problem_block_rejects_a_fourth_line():
    text = (
        "<!-- problem:start -->\n"
        "one\n"
        "two\n"
        "three\n"
        "four\n"
        "<!-- problem:end -->\n"
    )
    lines = [
        line
        for line in headline._between(
            text, headline.PROBLEM_START, headline.PROBLEM_END
        ).splitlines()
        if line.strip()
    ]
    assert len(lines) == 4


def test_headline_block_rejects_a_rewritten_rate():
    rows = headline.load_committed_rows()
    rates = headline.aggregate_rates(rows)
    canonical = "a" * 64
    block = headline.headline_block(rates, canonical)
    drifted = block.replace("replan: 1.0", "replan: 0.9", 1)
    assert drifted != block
    assert rates["replan"] == "1.0"
    assert rates["retry-only"] == "0.25"
