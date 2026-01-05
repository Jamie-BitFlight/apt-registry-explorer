"""
Integration tests against real Ubuntu APT repository.

These tests make real HTTP requests to Ubuntu's package mirrors
and should be run separately from unit tests using:
    pytest tests/test_integration.py -m integration -v
"""

import pytest

from apt_registry_explorer.discovery import RepositoryDiscovery
from apt_registry_explorer.packages import PackageIndex


@pytest.mark.integration
@pytest.mark.slow
def test_discover_ubuntu_jammy_release() -> None:
    """
    Test discovering Ubuntu 22.04 (Jammy) repository metadata.
    
    Validates:
    - Can connect to real Ubuntu repository
    - Can find Release file
    - Can extract architectures from Release file
    - Can extract components from Release file
    """
    # Use Ubuntu's official package mirror
    discovery = RepositoryDiscovery("http://archive.ubuntu.com/ubuntu/")
    
    # Find the Release file for jammy
    release_url = discovery.find_release_file("http://archive.ubuntu.com/ubuntu/dists/jammy/")
    
    assert release_url is not None, "Should find Release file for Ubuntu Jammy"
    assert "jammy" in release_url
    
    # Get architectures
    architectures = discovery.get_architectures(release_url)
    
    assert len(architectures) > 0, "Should find at least one architecture"
    assert "amd64" in architectures, "Ubuntu should support amd64"
    assert "arm64" in architectures, "Ubuntu should support arm64"
    
    # Get components
    components = discovery.get_components(release_url)
    
    assert len(components) > 0, "Should find at least one component"
    assert "main" in components, "Ubuntu should have main component"
    assert "universe" in components, "Ubuntu should have universe component"


@pytest.mark.integration
@pytest.mark.slow
def test_fetch_ubuntu_jammy_packages() -> None:
    """
    Test fetching and parsing real package data from Ubuntu Jammy.
    
    Validates:
    - Can fetch Packages file from real repository
    - Can parse package metadata correctly
    - Package data has expected fields
    """
    index = PackageIndex()
    
    # Fetch packages from Ubuntu Jammy main repository for amd64
    # Note: This is a real HTTP request that may be slow
    index.load_from_url("http://archive.ubuntu.com/ubuntu/", "amd64", "main")
    
    packages = index.get_all_packages()
    
    assert len(packages) > 100, "Ubuntu Jammy main should have many packages"
    
    # Try to find a well-known package
    bash_packages = index.filter_by_name("bash")
    
    assert len(bash_packages) > 0, "Should find bash package in Ubuntu"
    
    # Validate package metadata structure
    bash = bash_packages[0]
    assert bash.package == "bash"
    assert bash.version is not None and len(bash.version) > 0
    assert bash.architecture == "amd64"
    assert bash.description is not None


@pytest.mark.integration
@pytest.mark.slow
def test_filter_ubuntu_python_packages() -> None:
    """
    Test filtering packages using regex against real Ubuntu repository.
    
    Validates:
    - Regex filtering works with real data
    - Can find multiple python3 packages
    """
    index = PackageIndex()
    
    # Load packages from Ubuntu
    index.load_from_url("http://archive.ubuntu.com/ubuntu/", "amd64", "main")
    
    # Filter for python3 packages
    python_packages = index.filter_by_regex(r"^python3-")
    
    assert len(python_packages) > 10, "Should find multiple python3 packages"
    
    # All filtered packages should match the pattern
    for pkg in python_packages:
        assert pkg.package.startswith("python3-"), f"Package {pkg.package} should start with python3-"


@pytest.mark.integration
def test_ubuntu_repository_directory_listing() -> None:
    """
    Test that we can list directories in Ubuntu repository structure.
    
    Validates:
    - Can parse HTML directory listings
    - Can identify directories vs files
    """
    discovery = RepositoryDiscovery("http://archive.ubuntu.com/ubuntu/")
    
    # List the dists directory
    items = discovery.list_directory("http://archive.ubuntu.com/ubuntu/dists/")
    
    assert len(items) > 0, "Should find items in dists directory"
    
    # Look for jammy directory
    dir_names = [name for name, item_type in items if item_type == "dir"]
    
    assert "jammy" in dir_names, "Should find jammy distribution"
    assert "focal" in dir_names or "noble" in dir_names, "Should find other Ubuntu releases"
