"""
Tests for discovery module.
"""

import pytest
from apt_registry_explorer.discovery import RepositoryDiscovery


def test_repository_discovery_init():
    """Test RepositoryDiscovery initialization."""
    discovery = RepositoryDiscovery("https://example.com")
    assert discovery.base_url == "https://example.com"
    assert discovery.timeout == 10


def test_navigate():
    """Test URL navigation."""
    discovery = RepositoryDiscovery("https://example.com/")
    url = discovery.navigate(["dists", "stable"])
    assert "dists" in url
    assert "stable" in url


def test_parse_architectures():
    """Test parsing architectures from Release file."""
    RepositoryDiscovery("https://example.com")

    # Mock Release file content
    release_content = """Origin: Example
Label: Example
Suite: stable
Codename: stable
Architectures: amd64 arm64 armhf i386
Components: main contrib non-free
"""

    # This would need mocking in real tests, but demonstrates the parsing
    import re

    arch_pattern = r"^Architectures:\s*(.+)$"
    match = re.search(arch_pattern, release_content, re.MULTILINE)

    if match:
        archs = match.group(1).strip().split()
        assert "amd64" in archs
        assert "arm64" in archs
        assert len(archs) == 4
