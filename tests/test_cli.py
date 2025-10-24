"""
Tests for CLI module.
"""

import pytest
from click.testing import CliRunner
from apt_registry_explorer.cli import main


def test_cli_help():
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    
    assert result.exit_code == 0
    assert "apt-registry-explorer" in result.output


def test_query_help():
    """Test query command help."""
    runner = CliRunner()
    result = runner.invoke(main, ["query", "--help"])
    
    assert result.exit_code == 0
    assert "Query APT repository" in result.output


def test_discover_help():
    """Test discover command help."""
    runner = CliRunner()
    result = runner.invoke(main, ["discover", "--help"])
    
    assert result.exit_code == 0
    assert "discover repository" in result.output
