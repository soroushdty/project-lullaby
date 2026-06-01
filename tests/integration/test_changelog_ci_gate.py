import subprocess
import sys
from pathlib import Path


def _write_changelog(path: Path, targets_line: str = "tools/changelog_validator.py | +1 -0", date: str = "2026-06-01") -> None:
    path.write_text(
        "\n".join(
            [
                f"Date: {date}",
                "Spec: specs/000-changelog-creation/spec.md",
                "Summary: Integration validation",
                "Rationale: Verify CLI behavior",
                "Impact: Ensures CI pass/fail correctness",
                "Targets:",
                f"  {targets_line}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_cli_returns_zero_on_valid_input(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    _write_changelog(changelog)

    result = subprocess.run(
        [
            sys.executable,
            "tools/changelog_validator.py",
            "--changelog",
            str(changelog),
            "--spec-dir",
            str(specs_dir),
            "--spec-id",
            "000-changelog-creation",
            "--merge-date",
            "2026-06-01",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "PASS:" in result.stdout


def test_cli_returns_non_zero_on_policy_failure(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    _write_changelog(changelog, targets_line="bad-target-line")

    result = subprocess.run(
        [
            sys.executable,
            "tools/changelog_validator.py",
            "--changelog",
            str(changelog),
            "--spec-dir",
            str(specs_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "FAIL:" in result.stdout
    assert "E_TARGET_FORMAT" in result.stdout
