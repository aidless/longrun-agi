from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_evidence_site_exposes_sources_and_boundaries():
    page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    archive = (ROOT / "docs/archive/index.html").read_text(encoding="utf-8")
    control = (ROOT / "docs/control/index.html").read_text(encoding="utf-8")
    assert '<main id="main">' in page
    assert "MODEL GATE · HOLD" in page
    assert "190" in page
    assert "83/83" in page and "38/38" in page
    assert "Scripted-policy" in page
    assert "external benchmark" in (ROOT / "docs/assets/evidence.js").read_text(encoding="utf-8")
    assert "../artifacts/" in archive
    assert "data-package=\"P1\"" in control
    assert "data-package=\"P8\"" in control


def test_site_is_dependency_free_and_accessible():
    page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    css = (ROOT / "docs/assets/site.css").read_text(encoding="utf-8")
    script = (ROOT / "docs/assets/site.js").read_text(encoding="utf-8")
    assert "skip-link" in page
    assert 'aria-label="证据筛选"' in (ROOT / "docs/archive/index.html").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in css
    assert "https://cdn" not in page
    assert "fetch(" not in script


def test_governance_keeps_external_actions_gated():
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    application = (ROOT / "MODEL-GATE-APPLICATION.md").read_text(encoding="utf-8")
    assert "Do not access the sealed test split" in contributing
    assert "public GitHub security advisory" in security
    assert "Decision: HOLD" in application
    assert "Exact immutable revision" in application
    assert "Download authorization" in application


def test_pages_workflow_has_minimal_permissions_and_no_build_dependency():
    workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    assert "pages: write" in workflow
    assert "id-token: write" in workflow
    assert "actions/upload-pages-artifact@v4" in workflow
    assert "actions/deploy-pages@v4" in workflow
    assert "npm install" not in workflow
    assert "pip install" not in workflow


def test_issue_forms_and_pull_request_template_exist():
    expected = (
        ".github/ISSUE_TEMPLATE/bug.yml",
        ".github/ISSUE_TEMPLATE/evidence-proposal.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/pull_request_template.md",
        ".github/CODEOWNERS",
        "CHANGELOG.md",
        "ROADMAP.md",
    )
    for relative in expected:
        assert (ROOT / relative).is_file(), relative
