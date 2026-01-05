"""
Tests for CLI module.
"""

import pytest
from apt_registry_explorer.cli import app
from typer.testing import CliRunner


def test_cli_help() -> None:
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "apt-registry-explorer" in result.output or "Explore APT repositories" in result.output


def test_query_help() -> None:
    """Test query command help."""
    runner = CliRunner()
    result = runner.invoke(app, ["query", "--help"])

    assert result.exit_code == 0
    assert "Query APT repository" in result.output or "query" in result.output.lower()


def test_discover_help() -> None:
    """Test discover command help."""
    runner = CliRunner()
    result = runner.invoke(app, ["discover", "--help"])

    assert result.exit_code == 0
    assert "discover" in result.output.lower()
