from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_python_floor_and_cli_entrypoint():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["requires-python"] == ">=3.11"
    assert pyproject["project"]["scripts"]["reefiki"] == "scripts.reefiki:main"
    assert "pytest>=8.0" in pyproject["project"]["optional-dependencies"]["dev"]
    assert "pre-commit>=3.7" in pyproject["project"]["optional-dependencies"]["dev"]
    assert pyproject["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]


def test_license_and_readme_separate_code_and_wiki_rights():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Apache License" in license_text
    assert "Version 2.0" in license_text
    assert "Код REEFIKI: Apache License 2.0" in readme
    assert "Контент wiki-проектов принадлежит пользователю" in readme


def test_repository_gitattributes_normalizes_cross_platform_text_files():
    text = (ROOT / ".gitattributes").read_text(encoding="utf-8")

    assert "* text=auto eol=lf" in text
    assert "*.md text eol=lf" in text
    assert "*.yaml text eol=lf" in text
    assert "*.yml text eol=lf" in text
    assert "*.py text eol=lf" in text
    assert "*.ps1 text eol=crlf" in text
    assert "*.sqlite binary" in text


def test_pre_commit_local_hooks_use_python3_runtime():
    text = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert text.count("language_version: python3") == 2
    assert "entry: python scripts/reefiki.py secret-scan" in text
    assert "entry: python scripts/validate_frontmatter.py" in text


def test_cli_reports_python_version_before_importing_internal_modules():
    text = (ROOT / "scripts" / "reefiki.py").read_text(encoding="utf-8")

    guard_pos = text.index("if sys.version_info < (3, 11):")
    internal_import_pos = text.index("from reefiki_agent_readiness import")
    assert guard_pos < internal_import_pos
