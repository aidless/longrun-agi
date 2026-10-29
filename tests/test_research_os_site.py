import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ROUTES = ("index.html", "archive/index.html", "control/index.html", "map/index.html", "paper/index.html")


def read(relative: str) -> str:
    return (DOCS / relative).read_text(encoding="utf-8")


def test_all_research_os_routes_exist_and_share_assets():
    for route in ROUTES:
        page = read(route)
        assert 'lang="zh-CN"' in page
        assert 'data-page=' in page
        assert "evidence.js" in page
        assert "site.js" in page
        assert "site.css" in page
        assert "skip-link" in page
        assert "data-lang-toggle" in page


def test_public_evidence_is_single_versioned_local_source():
    evidence = read("assets/evidence.js")
    for token in ('release: "v0.1.0"', "tests: 190", "portfolioChecks: \"83/83\"", "artifactVersions: \"38/38\""):
        assert token in evidence
    for package in range(1, 9):
        assert f'id: "P{package}"' in evidence
    assert 'modelGate: "HOLD"' in evidence
    assert "sealed-not-accessed" in evidence
    assert "window.LONGRUN_EVIDENCE" in evidence


def test_chinese_is_default_and_english_choice_persists():
    script = read("assets/site.js")
    assert 'localStorage.getItem("longrun-language") || "zh"' in script
    assert 'localStorage.setItem("longrun-language"' in script
    assert 'document.documentElement.lang = language === "zh" ? "zh-CN" : "en"' in script
    assert "data-zh" in read("index.html")
    assert "我们没有证明" in read("index.html")


def test_every_chinese_marker_has_an_english_translation():
    pattern = re.compile(r'data-zh="[^"]*"')
    for route in ROUTES:
        page = read(route)
        for match in pattern.finditer(page):
            tail = page[match.end() : match.end() + 220]
            assert re.match(r'\s+data-en="[^"]*"', tail), (route, match.group())


def test_site_has_no_remote_runtime_dependency_or_analytics():
    combined = "\n".join(read(route) for route in ROUTES) + read("assets/site.css") + read("assets/site.js")
    assert "https://fonts" not in combined
    assert "fetch(" not in combined
    assert "gtag(" not in combined
    assert "analytics" not in combined.lower()
    assert "cdn." not in combined


def test_home_routes_to_all_five_experiences_and_states_boundaries():
    page = read("index.html")
    for href in ("archive/", "control/", "map/", "paper/"):
        assert f'href="{href}"' in page
    assert "我们验证的是证据链，不是 AGI" in page
    assert "No model evaluation" in page
    assert "MODEL GATE" in page


def test_archive_has_dossiers_sources_limits_and_hashes():
    page = read("archive/index.html")
    assert page.count('class="dossier"') >= 8
    assert "证据来源" in page
    assert "不支持的结论" in page
    assert re.search(r"[a-f0-9]{64}", page)
    assert "../artifacts/" in page


def test_control_room_has_all_packages_and_shared_counts():
    page = read("control/index.html")
    for package in range(1, 9):
        assert f'data-package="P{package}"' in page
    assert "190" in page
    assert "83/83" in page
    assert "38/38" in page
    assert "HOLD" in page


def test_map_has_eight_nodes_edges_and_accessible_mobile_path():
    page = read("map/index.html")
    for package in range(1, 9):
        assert f'data-node="P{package}"' in page
    assert page.count("data-edge=") >= 8
    assert '<ol class="mobile-path"' in page
    assert 'aria-label="研究关系图"' in page


def test_paper_has_verifiable_narrative_and_reproduction():
    page = read("paper/index.html")
    for section in ("problem", "method", "results", "negative-results", "limits", "reproduce"):
        assert f'id="{section}"' in page
    assert "make verify" in page
    assert "PORTFOLIO-STATUS.md" in page
    assert "MODEL-GATE.md" in page


def test_reduced_motion_keyboard_focus_and_mobile_layout_are_defined():
    css = read("assets/site.css")
    assert "prefers-reduced-motion" in css
    assert ":focus-visible" in css
    assert "@media (max-width: 760px)" in css
