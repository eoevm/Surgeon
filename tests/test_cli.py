"""Tests for CLI module."""

from click.testing import CliRunner
from reposurgeon.cli import main


def test_cli_help():
    """CLI help displays without error."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "RepoSurgeon" in result.output


def test_refactor_requires_description():
    """refactor command requires --description."""
    runner = CliRunner()
    result = runner.invoke(main, ["refactor", "https://github.com/user/repo"])
    assert result.exit_code != 0


def test_refactor_with_description():
    """refactor command accepts description."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "refactor",
            "https://github.com/user/repo",
            "-d",
            "Migrate to async/await",
            "--dry-run",
            "--model", "gpt-4o-mini",
        ],
    )
    assert result.exit_code == 0
    assert "RepoSurgeon" in result.output
    assert "Dry run mode" in result.output


def test_analyze_command():
    """analyze command works."""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", "https://github.com/user/repo"])
    assert result.exit_code == 0
    assert "Analyzing" in result.output
