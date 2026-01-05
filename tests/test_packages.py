"""
Tests for packages module.
"""

import pytest
from apt_registry_explorer.packages import PackageIndex, PackageMetadata


def test_package_metadata_creation():
    """Test PackageMetadata creation."""
    pkg = PackageMetadata(
        package="test-package", version="1.0.0", architecture="amd64", description="Test package"
    )

    assert pkg.package == "test-package"
    assert pkg.version == "1.0.0"
    assert pkg.architecture == "amd64"
    assert pkg.description == "Test package"


def test_package_metadata_to_dict():
    """Test converting PackageMetadata to dict."""
    pkg = PackageMetadata(package="test-package", version="1.0.0", architecture="amd64")

    pkg_dict = pkg.to_dict()
    assert pkg_dict["package"] == "test-package"
    assert pkg_dict["version"] == "1.0.0"
    assert pkg_dict["architecture"] == "amd64"


def test_package_metadata_to_json():
    """Test converting PackageMetadata to JSON."""
    pkg = PackageMetadata(package="test-package", version="1.0.0", architecture="amd64")

    json_str = pkg.to_json()
    assert "test-package" in json_str
    assert "1.0.0" in json_str


def test_parse_packages_file():
    """Test parsing Packages file."""
    content = """Package: test-package
Version: 1.0.0
Architecture: amd64
Maintainer: Test User <test@example.com>
Section: utils
Priority: optional
Description: A test package
 This is a longer description
 that spans multiple lines.

Package: another-package
Version: 2.0.0
Architecture: arm64
Section: libs
Description: Another package

"""

    index = PackageIndex()
    packages = index.parse_packages_file(content)

    assert len(packages) == 2
    assert packages[0].package == "test-package"
    assert packages[0].version == "1.0.0"
    assert packages[0].architecture == "amd64"
    assert packages[1].package == "another-package"
    assert packages[1].version == "2.0.0"


def test_filter_by_name():
    """Test filtering packages by name."""
    index = PackageIndex()
    index.packages = [
        PackageMetadata("pkg1", "1.0", "amd64"),
        PackageMetadata("pkg2", "2.0", "amd64"),
        PackageMetadata("pkg1", "1.1", "arm64"),
    ]

    filtered = index.filter_by_name("pkg1")
    assert len(filtered) == 2
    assert all(p.package == "pkg1" for p in filtered)


def test_filter_by_regex():
    """Test filtering packages by regex."""
    index = PackageIndex()
    index.packages = [
        PackageMetadata("python-package", "1.0", "amd64"),
        PackageMetadata("python-lib", "2.0", "amd64"),
        PackageMetadata("other-pkg", "1.0", "amd64"),
    ]

    filtered = index.filter_by_regex("^python-")
    assert len(filtered) == 2
    assert all(p.package.startswith("python-") for p in filtered)


def test_filter_by_version():
    """Test filtering packages by version."""
    index = PackageIndex()
    index.packages = [
        PackageMetadata("pkg", "1.0", "amd64"),
        PackageMetadata("pkg", "2.0", "amd64"),
        PackageMetadata("pkg", "3.0", "amd64"),
    ]

    filtered = index.filter_by_version(">=2.0")
    assert len(filtered) == 2
    assert all(p.version >= "2.0" for p in filtered)
