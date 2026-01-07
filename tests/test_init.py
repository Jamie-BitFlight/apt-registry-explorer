"""
Tests for __init__ module.
"""

from apt_registry_explorer import __version__


def test_version_exists() -> None:
    """Test that version is defined."""
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_version_format() -> None:
    """Test that version follows semantic versioning format."""
    # Should be in format like "0.1.0" or "0.1.0.dev1"
    parts = __version__.split(".")
    assert len(parts) >= 2
    # First part should be digit
    assert parts[0].isdigit() or parts[0].startswith("0")
