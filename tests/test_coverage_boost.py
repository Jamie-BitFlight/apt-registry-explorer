"""Additional tests to increase coverage for apt-registry-explorer."""

import json
from unittest.mock import Mock, patch

import httpx
from apt_registry_explorer.cli import SourceParser
from apt_registry_explorer.discovery import RepositoryDiscovery
from apt_registry_explorer.packages import PackageIndex, PackageMetadata
from apt_registry_explorer.sources import SourcesBuilder


class TestSourceParserMethods:
    """Test SourceParser static methods."""

    def test_parse_source_url_only(self):  # noqa: PLR6301  # noqa: PLR6301
        """Test parsing a simple URL source."""
        url, suite = SourceParser.parse_source("http://archive.ubuntu.com/ubuntu")

        assert url == "http://archive.ubuntu.com/ubuntu"
        assert suite == "stable"


class TestRepositoryDiscoveryMethods:
    """Test RepositoryDiscovery methods."""

    def test_init_with_timeout(self):  # noqa: PLR6301
        """Test initialization with custom timeout."""
        discovery = RepositoryDiscovery("http://example.com/repo", timeout=30)

        assert discovery.base_url == "http://example.com/repo"
        assert discovery.timeout == 30

    @patch("apt_registry_explorer.discovery.httpx.Client")
    def test_list_directory_with_files(self, mock_client_class):  # noqa: PLR6301
        """Test listing directory contents."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '<html><a href="file1.txt">file1</a><a href="dir1/">dir1</a></html>'
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        discovery = RepositoryDiscovery("http://example.com/repo")
        result = discovery.list_directory("http://example.com/repo/test")

        assert len(result) > 0
        # Check for directory and file types
        assert any(item_type == "dir" for _, item_type in result)

    @patch("apt_registry_explorer.discovery.httpx.Client")
    def test_find_release_file_inrelease(self, mock_client_class):  # noqa: PLR6301
        """Test finding InRelease file."""
        mock_client = Mock()

        def mock_get(url):
            mock_response = Mock()
            if "InRelease" in url:
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_response.text = "Release content"
            elif url.endswith("/"):
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_response.text = '<a href="InRelease">InRelease</a>'
            else:
                mock_response.status_code = 404
                mock_response.raise_for_status = Mock(
                    side_effect=httpx.HTTPStatusError("Not found", request=Mock(), response=Mock())
                )
            return mock_response

        mock_client.get.side_effect = mock_get
        mock_client_class.return_value = mock_client

        discovery = RepositoryDiscovery("http://example.com/repo")
        result = discovery.find_release_file("http://example.com/repo/dists/stable/")

        assert result is not None
        assert "InRelease" in result

    @patch("apt_registry_explorer.discovery.httpx.Client")
    def test_find_release_file_release(self, mock_client_class):  # noqa: PLR6301
        """Test finding Release file when InRelease doesn't exist."""
        mock_client = Mock()

        def mock_get(url):
            mock_response = Mock()
            if "InRelease" in url:
                mock_response.status_code = 404
                mock_response.raise_for_status = Mock(
                    side_effect=httpx.HTTPStatusError("Not found", request=Mock(), response=Mock())
                )
            elif "Release" in url:
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_response.text = "Release content"
            elif url.endswith("/"):
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_response.text = '<a href="Release">Release</a>'
            else:
                mock_response.status_code = 404
                mock_response.raise_for_status = Mock(
                    side_effect=httpx.HTTPStatusError("Not found", request=Mock(), response=Mock())
                )
            return mock_response

        mock_client.get.side_effect = mock_get
        mock_client_class.return_value = mock_client

        discovery = RepositoryDiscovery("http://example.com/repo")
        result = discovery.find_release_file("http://example.com/repo/dists/stable/")

        assert result is not None
        assert "Release" in result

    @patch("apt_registry_explorer.discovery.httpx.Client")
    def test_get_architectures(self, mock_client_class):  # noqa: PLR6301
        """Test extracting architectures from Release file."""
        release_content = """Origin: Ubuntu
Codename: jammy
Architectures: amd64 arm64 i386
Components: main restricted
"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = release_content
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        discovery = RepositoryDiscovery("http://archive.ubuntu.com/ubuntu")
        result = discovery.get_architectures("http://archive.ubuntu.com/ubuntu/dists/jammy/Release")

        assert "amd64" in result
        assert "arm64" in result
        assert "i386" in result

    @patch("apt_registry_explorer.discovery.httpx.Client")
    def test_navigate(self, mock_client_class):  # noqa: PLR6301
        """Test navigating repository structure."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '<html><a href="InRelease">InRelease</a></html>'
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        discovery = RepositoryDiscovery("http://example.com/repo")
        result = discovery.navigate("/dists/stable")

        assert isinstance(result, str)
        # The method returns a URL, not necessarily containing the input path
        assert "http://example.com/repo" in result


class TestPackageIndexMethods:
    """Test PackageIndex additional methods."""

    def test_init_empty(self):  # noqa: PLR6301
        """Test initializing empty package index."""
        index = PackageIndex()
        assert index.packages == []

    def test_filter_by_name_empty_result(self):  # noqa: PLR6301
        """Test filtering by name with no matches."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(
                package="nginx",
                version="1.20.0",
                architecture="amd64",
                maintainer="Test",
                description="Server",
            )
        ]

        result = index.filter_by_name("apache2")

        assert len(result) == 0

    def test_filter_by_regex_match(self):  # noqa: PLR6301
        """Test filtering by regex with matches."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(
                package="python3-django",
                version="3.2.0",
                architecture="all",
                maintainer="Test",
                description="Framework",
            ),
            PackageMetadata(
                package="python3-flask",
                version="2.0.0",
                architecture="all",
                maintainer="Test",
                description="Framework",
            ),
            PackageMetadata(
                package="ruby-rails",
                version="6.0.0",
                architecture="all",
                maintainer="Test",
                description="Framework",
            ),
        ]

        result = index.filter_by_regex("^python3-")

        assert len(result) == 2

    def test_filter_by_version_invalid_operator(self):  # noqa: PLR6301
        """Test filtering by version with invalid operator."""
        index = PackageIndex()
        index.packages = [
            PackageMetadata(
                package="nginx",
                version="1.20.0",
                architecture="amd64",
                maintainer="Test",
                description="Server",
            )
        ]

        # Invalid operator should return empty list
        result = index.filter_by_version("~1.20.0")

        assert len(result) == 0


class TestPackageMetadataJSON:
    """Test PackageMetadata JSON serialization."""

    def test_to_json_valid_format(self):  # noqa: PLR6301
        """Test to_json produces valid JSON."""
        package = PackageMetadata(
            package="nginx",
            version="1.20.0",
            architecture="amd64",
            maintainer="Ubuntu Developers",
            description="HTTP server",
        )

        result = package.to_json()
        data = json.loads(result)

        assert data["package"] == "nginx"
        assert data["version"] == "1.20.0"
        assert data["architecture"] == "amd64"

    def test_to_dict_all_optional_fields(self):  # noqa: PLR6301
        """Test to_dict with optional fields."""
        package = PackageMetadata(
            package="nginx",
            version="1.20.0",
            architecture="amd64",
            maintainer="Ubuntu Developers",
            description="HTTP server",
            depends="libc6",
            recommends="nginx-common",
            suggests="nginx-doc",
            section="web",
            priority="optional",
            homepage="https://nginx.org",
            filename="nginx.deb",
            size="100000",
            sha256="abc123",
        )

        result = package.to_dict()

        assert result["depends"] == "libc6"
        assert result["recommends"] == "nginx-common"
        assert result["homepage"] == "https://nginx.org"


class TestSourcesBuilderMethods:
    """Test SourcesBuilder methods for additional coverage."""

    def test_add_source(self):  # noqa: PLR6301
        """Test adding a source."""
        builder = SourcesBuilder()
        builder.add_source("deb", "http://example.com/repo", "stable", ["main", "contrib"])

        assert len(builder.entries) == 1
        assert builder.entries[0].url == "http://example.com/repo"

    def test_parse_deb_line_with_options(self):  # noqa: PLR6301
        """Test parsing deb line with options."""
        builder = SourcesBuilder()
        result = builder.parse_deb_line(
            "deb [arch=amd64 signed-by=/usr/share/keyrings/test.gpg] http://example.com/repo stable main"
        )

        assert result is not None
        assert result.url == "http://example.com/repo"
        assert result.suite == "stable"
        assert result.options is not None


class TestInitModule:
    """Test __init__ module exports."""

    def test_version_attribute_exists(self):  # noqa: PLR6301  # noqa: PLR6301
        """Test that __version__ is accessible."""
        import apt_registry_explorer  # noqa: PLC0415

        assert hasattr(apt_registry_explorer, "__version__")
        assert isinstance(apt_registry_explorer.__version__, str)
