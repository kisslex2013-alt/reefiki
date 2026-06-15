from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflow_runs_core_verification_gates():
    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "timeout-minutes: 10" in text
    assert "contents: read" in text
    assert "runs-on: ${{ matrix.os }}" in text
    assert "fail-fast: false" in text
    assert "ubuntu-latest" in text
    assert "windows-latest" in text
    assert "macos-latest" in text
    assert "shell: pwsh" in text
    assert "python scripts/validate_frontmatter.py" in text
    assert '"projects/_template/wiki/*.md" "projects/reefiki/wiki/*.md" "projects/metrica/wiki/*.md"' in text
    assert "'projects/*/wiki/*.md'" not in text
    assert "xargs" not in text
    assert "python -m pytest" in text
    assert "python scripts/reefiki.py memory golden --project reefiki --format json" in text
