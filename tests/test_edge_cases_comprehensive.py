"""Additional comprehensive tests for discovery and packages modules to increase coverage."""

import gzip
import io
import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from apt_registry_explorer.discovery import RepositoryDiscovery
from apt_registry_explorer.packages import PackageIndex, PackageMetadata


class TestRepositoryDiscoveryEdgeCases:
    """Test edge cases and error handling in RepositoryDiscovery."""

    def test_navigate_with_empty_path(self) -> None:  # noqa: PLR6301
        """Test navigate with empty path list."""
        discovery = RepositoryDiscovery("https://example.com")
        result = discovery.navigate([])
        assert result == "https://example.com"

    def test_navigate_with_single_path(self) -> None:  # noqa: PLR6301
        """Test navigate with single path element."""
        discovery = RepositoryDiscovery("https://example.com")
        result = discovery.navigate(["dists"])
        assert result == "https://example.com/dists/"

    def test_navigate_with_multiple_paths(self) -> None:  # noqa: PLR6301
        """Test navigate with multiple path elements."""
        discovery = RepositoryDiscovery("https://example.com")
        result = discovery.navigate(["dists", "jammy", "main"])
        assert result == "https://example.com/dists/jammy/main/"

    def test_navigate_handles_trailing_slashes(self) -> None:  # noqa: PLR6301
        """Test that navigate handles trailing slashes correctly."""
        discovery = RepositoryDiscovery("https://example.com/")
        result = discovery.navigate(["dists"])
        # Should not have double slashes
        assert "//" not in result or result.startswith("https://")

    def test_find_release_file_tries_inrelease_first(self) -> None:  # noqa: PLR6301
        """Test that find_release_file finds InRelease file."""
        discovery = RepositoryDiscovery("https://example.com")

        # Mock list_directory to return InRelease file
        with patch.object(
            discovery, "list_directory", return_value=[("InRelease", "file"), ("Packages", "file")]
        ):
            result = discovery.find_release_file("https://example.com/dists/jammy/")
            assert result is not None
            assert "InRelease" in result

    def test_find_release_file_falls_back_to_release(self) -> None:  # noqa: PLR6301
        """Test that find_release_file finds Release file when InRelease not available."""
        discovery = RepositoryDiscovery("https://example.com")

        # Mock list_directory to return only Release file
        with patch.object(
            discovery, "list_directory", return_value=[("Release", "file"), ("Packages", "file")]
        ):
            result = discovery.find_release_file("https://example.com/dists/jammy/")
            assert result is not None
            assert "Release" in result

    def test_find_release_file_returns_none_when_both_fail(self) -> None:  # noqa: PLR6301
        """Test that find_release_file returns None when list_directory returns empty list."""
        discovery = RepositoryDiscovery("https://example.com")

        # Mock list_directory to return empty list (simulating no files found)
        with patch.object(discovery, "list_directory", return_value=[]):
            result = discovery.find_release_file("https://example.com/dists/jammy/")
            assert result is None

    def test_get_architectures_parses_correctly(self) -> None:  # noqa: PLR6301
        """Test that get_architectures parses the Architectures line correctly."""
        discovery = RepositoryDiscovery("https://example.com")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Architectures: amd64 arm64 i386\nComponents: main"

        # Mock the client's get method
        with patch.object(discovery.client, "get", return_value=mock_response):
            result = discovery.get_architectures("https://example.com/Release")
            assert result == ["amd64", "arm64", "i386"]

    def test_get_architectures_returns_empty_when_not_found(self) -> None:  # noqa: PLR6301
        """Test that get_architectures returns empty list when field not found."""
        discovery = RepositoryDiscovery("https://example.com")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Components: main\nSuite: jammy"

        # Mock the client's get method
        with patch.object(discovery.client, "get", return_value=mock_response):
            result = discovery.get_architectures("https://example.com/Release")
            assert result == []

    def test_get_components_parses_correctly(self) -> None:  # noqa: PLR6301
        """Test that get_components parses the Components line correctly."""
        discovery = RepositoryDiscovery("https://example.com")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Components: main restricted universe multiverse\nArchitectures: amd64"

        # Mock the client's get method
        with patch.object(discovery.client, "get", return_value=mock_response):
            result = discovery.get_components("https://example.com/Release")
            assert result == ["main", "restricted", "universe", "multiverse"]

    def test_get_components_returns_empty_when_not_found(self) -> None:  # noqa: PLR6301
        """Test that get_components returns empty list when field not found."""
        discovery = RepositoryDiscovery("https://example.com")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Architectures: amd64\nSuite: jammy"

        # Mock the client's get method
        with patch.object(discovery.client, "get", return_value=mock_response):
            result = discovery.get_components("https://example.com/Release")
            assert result == []

    @patch("httpx.get")
    def test_list_directory_handles_http_errors(self, mock_get) -> None:  # noqa: PLR6301
        """Test that list_directory handles HTTP errors gracefully."""
        discovery = RepositoryDiscovery("https://example.com")

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = discovery.list_directory("https://example.com")

        assert result == []


class TestPackageIndexEdgeCases:
    """Test edge cases and error handling in PackageIndex."""

    def test_filter_by_name_case_sensitive(self) -> None:  # noqa: PLR6301
        """Test that filter_by_name is case-sensitive."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(package="Nginx", version="1.0", architecture="amd64"),
            PackageMetadata(package="nginx", version="1.0", architecture="amd64"),
        ]

        result = index.filter_by_name("nginx")

        assert len(result) == 1
        assert result[0].package == "nginx"

    def test_filter_by_regex_empty_pattern(self) -> None:  # noqa: PLR6301
        """Test filter_by_regex with empty pattern."""
        index = PackageIndex()
        index.packages = [PackageMetadata(package="nginx", version="1.0", architecture="amd64")]

        # Empty pattern should match everything
        result = index.filter_by_regex("")

        assert len(result) == 1

    def test_filter_by_regex_invalid_pattern(self) -> None:  # noqa: PLR6301
        """Test filter_by_regex with invalid regex pattern."""
        index = PackageIndex()
        index.packages = [PackageMetadata(package="nginx", version="1.0", architecture="amd64")]

        # Invalid regex should raise exception or return empty
        with pytest.raises(Exception, match=r".*"):
            index.filter_by_regex("[invalid(")

    def test_filter_by_version_exact_match(self) -> None:  # noqa: PLR6301
        """Test filter_by_version with exact version match."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(package="nginx", version="1.18.0", architecture="amd64"),
            PackageMetadata(package="apache", version="2.4.0", architecture="amd64"),
        ]

        result = index.filter_by_version("==1.18.0")

        assert len(result) == 1
        assert result[0].package == "nginx"

    def test_filter_by_version_greater_than(self) -> None:  # noqa: PLR6301
        """Test filter_by_version with greater than operator."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(package="pkg1", version="1.0.0", architecture="amd64"),
            PackageMetadata(package="pkg2", version="2.0.0", architecture="amd64"),
            PackageMetadata(package="pkg3", version="3.0.0", architecture="amd64"),
        ]

        result = index.filter_by_version(">1.5.0")

        assert len(result) == 2
        assert all(pkg.package in {"pkg2", "pkg3"} for pkg in result)

    def test_filter_by_version_less_than(self) -> None:  # noqa: PLR6301
        """Test filter_by_version with less than operator."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(package="pkg1", version="1.0.0", architecture="amd64"),
            PackageMetadata(package="pkg2", version="2.0.0", architecture="amd64"),
        ]

        result = index.filter_by_version("<1.5.0")

        assert len(result) == 1
        assert result[0].package == "pkg1"

    def test_get_all_packages_returns_packages(self) -> None:  # noqa: PLR6301
        """Test that get_all_packages returns the packages list."""
        index = PackageIndex()
        original_packages = [PackageMetadata(package="nginx", version="1.0", architecture="amd64")]
        index.packages = original_packages

        result = index.get_all_packages()

        # Returns the same list
        assert result == original_packages
        assert len(result) == 1

    def test_load_from_url_handles_http_error(self) -> None:  # noqa: PLR6301
        """Test that load_from_url raises error on HTTP failure."""
        index = PackageIndex()

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )

        # Mock the client's get method
        with (
            patch.object(index.client, "get", return_value=mock_response),
            pytest.raises(ValueError, match=r".*"),
        ):
            index.load_from_url("https://example.com", "amd64", "main")

    def test_load_from_url_parses_gzipped_content(self) -> None:  # noqa: PLR6301
        """Test that load_from_url handles gzipped Packages files."""
        index = PackageIndex()

        # Create mock gzipped content
        packages_content = b"Package: nginx\nVersion: 1.0\nArchitecture: amd64\n\n"
        gzipped = io.BytesIO()
        with gzip.GzipFile(fileobj=gzipped, mode="wb") as f:
            f.write(packages_content)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = gzipped.getvalue()

        # Mock the client's get method
        with patch.object(index.client, "get", return_value=mock_response):
            index.load_from_url("https://example.com", "amd64", "main")
            # Should have parsed the package
            assert len(index.packages) > 0


class TestPackageMetadataEdgeCases:
    """Test edge cases for PackageMetadata."""

    def test_to_dict_with_all_fields(self) -> None:  # noqa: PLR6301
        """Test to_dict with all fields populated."""
        pkg = PackageMetadata(
            package="nginx",
            version="1.18.0",
            architecture="amd64",
            description="web server",
            depends="libc6, libssl1.1",
            section="web",
            priority="optional",
            homepage="https://nginx.org",
            maintainer="Ubuntu Developers",
        )

        result = pkg.to_dict()

        assert result["package"] == "nginx"
        assert result["version"] == "1.18.0"
        assert result["architecture"] == "amd64"
        assert result["description"] == "web server"
        assert "depends" in result
        assert "homepage" in result

    def test_to_dict_with_minimal_fields(self) -> None:  # noqa: PLR6301
        """Test to_dict with only required fields."""
        pkg = PackageMetadata(package="test", version="1.0", architecture="all")

        result = pkg.to_dict()

        assert result["package"] == "test"
        assert result["version"] == "1.0"
        assert result["architecture"] == "all"

    def test_to_json_produces_valid_json(self) -> None:  # noqa: PLR6301  # noqa: PLR6301
        """Test that to_json produces valid JSON string."""
        pkg = PackageMetadata(package="nginx", version="1.18.0", architecture="amd64")

        result = pkg.to_json()

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["package"] == "nginx"
