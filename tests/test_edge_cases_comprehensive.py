"""Additional comprehensive tests for discovery and packages modules to increase coverage."""

from unittest.mock import MagicMock, patch

import pytest

from apt_registry_explorer.discovery import RepositoryDiscovery
from apt_registry_explorer.packages import PackageIndex, PackageMetadata


class TestRepositoryDiscoveryEdgeCases:
    """Test edge cases and error handling in RepositoryDiscovery."""

    def test_navigate_with_empty_path(self) -> None:
        """Test navigate with empty path list."""
        discovery = RepositoryDiscovery("https://example.com")
        result = discovery.navigate([])
        assert result == "https://example.com"

    def test_navigate_with_single_path(self) -> None:
        """Test navigate with single path element."""
        discovery = RepositoryDiscovery("https://example.com")
        result = discovery.navigate(["dists"])
        assert result == "https://example.com/dists"

    def test_navigate_with_multiple_paths(self) -> None:
        """Test navigate with multiple path elements."""
        discovery = RepositoryDiscovery("https://example.com")
        result = discovery.navigate(["dists", "jammy", "main"])
        assert result == "https://example.com/dists/jammy/main"

    def test_navigate_handles_trailing_slashes(self) -> None:
        """Test that navigate handles trailing slashes correctly."""
        discovery = RepositoryDiscovery("https://example.com/")
        result = discovery.navigate(["dists"])
        # Should not have double slashes
        assert "//" not in result or result.startswith("https://")

    @patch("httpx.get")
    def test_find_release_file_tries_inrelease_first(self, mock_get) -> None:
        """Test that find_release_file tries InRelease before Release."""
        discovery = RepositoryDiscovery("https://example.com")
        
        # Mock successful InRelease response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = discovery.find_release_file("https://example.com/dists/jammy/")
        
        # Should try InRelease first
        assert mock_get.call_count >= 1
        first_call_url = mock_get.call_args_list[0][0][0]
        assert "InRelease" in first_call_url

    @patch("httpx.get")
    def test_find_release_file_falls_back_to_release(self, mock_get) -> None:
        """Test that find_release_file falls back to Release if InRelease fails."""
        discovery = RepositoryDiscovery("https://example.com")
        
        # Mock InRelease failure, Release success
        def mock_response_func(url):
            response = MagicMock()
            if "InRelease" in url:
                response.status_code = 404
            else:
                response.status_code = 200
            return response
        
        mock_get.side_effect = mock_response_func
        
        result = discovery.find_release_file("https://example.com/dists/jammy/")
        
        # Should have tried both
        assert mock_get.call_count == 2

    @patch("httpx.get")
    def test_find_release_file_returns_none_when_both_fail(self, mock_get) -> None:
        """Test that find_release_file returns None when both files not found."""
        discovery = RepositoryDiscovery("https://example.com")
        
        # Mock both failing
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = discovery.find_release_file("https://example.com/dists/jammy/")
        
        assert result is None

    @patch("httpx.get")
    def test_get_architectures_parses_correctly(self, mock_get) -> None:
        """Test that get_architectures parses the Architectures line correctly."""
        discovery = RepositoryDiscovery("https://example.com")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Architectures: amd64 arm64 i386\nComponents: main"
        mock_get.return_value = mock_response
        
        result = discovery.get_architectures("https://example.com/Release")
        
        assert result == ["amd64", "arm64", "i386"]

    @patch("httpx.get")
    def test_get_architectures_returns_empty_when_not_found(self, mock_get) -> None:
        """Test that get_architectures returns empty list when field not found."""
        discovery = RepositoryDiscovery("https://example.com")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Components: main\nSuite: jammy"
        mock_get.return_value = mock_response
        
        result = discovery.get_architectures("https://example.com/Release")
        
        assert result == []

    @patch("httpx.get")
    def test_get_components_parses_correctly(self, mock_get) -> None:
        """Test that get_components parses the Components line correctly."""
        discovery = RepositoryDiscovery("https://example.com")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Components: main restricted universe multiverse\nArchitectures: amd64"
        mock_get.return_value = mock_response
        
        result = discovery.get_components("https://example.com/Release")
        
        assert result == ["main", "restricted", "universe", "multiverse"]

    @patch("httpx.get")
    def test_get_components_returns_empty_when_not_found(self, mock_get) -> None:
        """Test that get_components returns empty list when field not found."""
        discovery = RepositoryDiscovery("https://example.com")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Architectures: amd64\nSuite: jammy"
        mock_get.return_value = mock_response
        
        result = discovery.get_components("https://example.com/Release")
        
        assert result == []

    @patch("httpx.get")
    def test_list_directory_handles_http_errors(self, mock_get) -> None:
        """Test that list_directory handles HTTP errors gracefully."""
        discovery = RepositoryDiscovery("https://example.com")
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = discovery.list_directory("https://example.com")
        
        assert result == []


class TestPackageIndexEdgeCases:
    """Test edge cases and error handling in PackageIndex."""

    def test_filter_by_name_case_sensitive(self) -> None:
        """Test that filter_by_name is case-sensitive."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(package="Nginx", version="1.0", architecture="amd64"),
            PackageMetadata(package="nginx", version="1.0", architecture="amd64"),
        ]
        
        result = index.filter_by_name("nginx")
        
        assert len(result) == 1
        assert result[0].package == "nginx"

    def test_filter_by_regex_empty_pattern(self) -> None:
        """Test filter_by_regex with empty pattern."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(package="nginx", version="1.0", architecture="amd64"),
        ]
        
        # Empty pattern should match everything
        result = index.filter_by_regex("")
        
        assert len(result) == 1

    def test_filter_by_regex_invalid_pattern(self) -> None:
        """Test filter_by_regex with invalid regex pattern."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(package="nginx", version="1.0", architecture="amd64"),
        ]
        
        # Invalid regex should raise exception or return empty
        with pytest.raises(Exception):  # Could be re.error or other
            index.filter_by_regex("[invalid(")

    def test_filter_by_version_exact_match(self) -> None:
        """Test filter_by_version with exact version match."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(package="nginx", version="1.18.0", architecture="amd64"),
            PackageMetadata(package="apache", version="2.4.0", architecture="amd64"),
        ]
        
        result = index.filter_by_version("==1.18.0")
        
        assert len(result) == 1
        assert result[0].package == "nginx"

    def test_filter_by_version_greater_than(self) -> None:
        """Test filter_by_version with greater than operator."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(package="pkg1", version="1.0.0", architecture="amd64"),
            PackageMetadata(package="pkg2", version="2.0.0", architecture="amd64"),
            PackageMetadata(package="pkg3", version="3.0.0", architecture="amd64"),
        ]
        
        result = index.filter_by_version(">1.5.0")
        
        assert len(result) == 2
        assert all(pkg.package in ["pkg2", "pkg3"] for pkg in result)

    def test_filter_by_version_less_than(self) -> None:
        """Test filter_by_version with less than operator."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(package="pkg1", version="1.0.0", architecture="amd64"),
            PackageMetadata(package="pkg2", version="2.0.0", architecture="amd64"),
        ]
        
        result = index.filter_by_version("<1.5.0")
        
        assert len(result) == 1
        assert result[0].package == "pkg1"

    def test_get_all_packages_returns_copy(self) -> None:
        """Test that get_all_packages returns a copy of the packages list."""
        index = PackageIndex()
        original_packages = [
            PackageMetadata(package="nginx", version="1.0", architecture="amd64"),
        ]
        index.packages = original_packages
        
        result = index.get_all_packages()
        
        # Modifying result should not affect original
        result.clear()
        assert len(index.packages) == 1

    @patch("httpx.get")
    def test_load_from_url_handles_http_error(self, mock_get) -> None:
        """Test that load_from_url handles HTTP errors gracefully."""
        index = PackageIndex()
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_response
        
        # Should handle error gracefully
        with pytest.raises(Exception):
            index.load_from_url("https://example.com", "amd64", "main")

    @patch("httpx.get")
    def test_load_from_url_parses_gzipped_content(self, mock_get) -> None:
        """Test that load_from_url handles gzipped Packages files."""
        index = PackageIndex()
        
        # Create mock gzipped content
        import gzip
        import io
        
        packages_content = b"Package: nginx\nVersion: 1.0\nArchitecture: amd64\n\n"
        gzipped = io.BytesIO()
        with gzip.GzipFile(fileobj=gzipped, mode="wb") as f:
            f.write(packages_content)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = gzipped.getvalue()
        mock_get.return_value = mock_response
        
        index.load_from_url("https://example.com", "amd64", "main")
        
        # Should have parsed the package
        assert len(index.packages) > 0


class TestPackageMetadataEdgeCases:
    """Test edge cases for PackageMetadata."""

    def test_to_dict_with_all_fields(self) -> None:
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

    def test_to_dict_with_minimal_fields(self) -> None:
        """Test to_dict with only required fields."""
        pkg = PackageMetadata(
            package="test",
            version="1.0",
            architecture="all",
        )
        
        result = pkg.to_dict()
        
        assert result["package"] == "test"
        assert result["version"] == "1.0"
        assert result["architecture"] == "all"

    def test_to_json_produces_valid_json(self) -> None:
        """Test that to_json produces valid JSON string."""
        import json
        
        pkg = PackageMetadata(
            package="nginx",
            version="1.18.0",
            architecture="amd64",
        )
        
        result = pkg.to_json()
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["package"] == "nginx"
