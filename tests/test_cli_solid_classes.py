"""Comprehensive tests for CLI SOLID classes with proper mocking and fixtures."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from apt_registry_explorer.cli import (
    ArchitectureLister,
    OutputFormat,
    PackageQuerier,
    RepositoryExplorer,
    SourceParser,
    SourcesFormat,
    app,
)
from apt_registry_explorer.packages import PackageMetadata
from typer.testing import CliRunner

# ===== Fixtures =====


@pytest.fixture
def fixtures_dir() -> Path:
    """Get fixtures directory path."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def release_file_content(fixtures_dir: Path) -> str:
    """Load release file fixture."""
    return (fixtures_dir / "release_file.txt").read_text()


@pytest.fixture
def packages_file_content(fixtures_dir: Path) -> str:
    """Load packages file fixture."""
    return (fixtures_dir / "packages_file.txt").read_text()


@pytest.fixture
def mock_discovery():
    """Create a mocked RepositoryDiscovery instance."""
    with patch("apt_registry_explorer.cli.RepositoryDiscovery") as mock:
        discovery_instance = MagicMock()
        mock.return_value = discovery_instance
        yield discovery_instance


@pytest.fixture
def mock_package_index():
    """Create a mocked PackageIndex instance."""
    with patch("apt_registry_explorer.cli.PackageIndex") as mock:
        index_instance = MagicMock()
        mock.return_value = index_instance
        yield index_instance


@pytest.fixture
def sample_packages() -> list[PackageMetadata]:
    """Create sample package metadata for testing."""
    return [
        PackageMetadata(
            package="nginx",
            version="1.18.0-0ubuntu1",
            architecture="amd64",
            description="small, powerful, scalable web/proxy server",
            depends="libc6, libssl1.1",
            section="web",
            priority="optional",
        ),
        PackageMetadata(
            package="python3",
            version="3.10.4-0ubuntu2",
            architecture="amd64",
            description="interactive high-level object-oriented language",
            depends="python3.10",
            section="python",
            priority="important",
        ),
        PackageMetadata(
            package="python3-pip",
            version="22.0.2+dfsg-1",
            architecture="all",
            description="Python package installer",
            depends="python3",
            section="python",
            priority="optional",
        ),
    ]


# ===== SourceParser Tests =====


class TestSourceParser:
    """Test SourceParser class."""

    def test_parse_url_source(self) -> None:  # noqa: PLR6301
        """Test parsing plain URL source."""
        url, suite = SourceParser.parse_source("https://example.com/ubuntu")
        assert url == "https://example.com/ubuntu"
        assert suite == "stable"

    def test_parse_deb_line_source(self) -> None:  # noqa: PLR6301
        """Test parsing deb line source."""
        deb_line = "deb https://example.com/ubuntu jammy main"
        url, suite = SourceParser.parse_source(deb_line)
        assert url == "https://example.com/ubuntu"
        assert suite == "jammy"

    def test_parse_deb_line_with_options(self) -> None:  # noqa: PLR6301
        """Test parsing deb line with options."""
        deb_line = "deb [arch=amd64] https://example.com/ubuntu jammy main restricted"
        url, suite = SourceParser.parse_source(deb_line)
        assert url == "https://example.com/ubuntu"
        assert suite == "jammy"

    def test_parse_invalid_deb_line_exits(self) -> None:  # noqa: PLR6301
        """Test that invalid deb line raises Exit."""
        with pytest.raises(SystemExit):
            SourceParser.parse_source("deb invalid")


# ===== ArchitectureLister Tests =====


class TestArchitectureLister:
    """Test ArchitectureLister class."""

    def test_list_architectures_json(self, mock_discovery, capsys) -> None:  # noqa: PLR6301
        """Test listing architectures in JSON format."""
        mock_discovery.find_release_file.return_value = "https://example.com/Release"
        mock_discovery.get_architectures.return_value = ["amd64", "arm64", "i386"]

        ArchitectureLister.list_architectures("https://example.com", "jammy", OutputFormat.JSON)

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output == {"architectures": ["amd64", "arm64", "i386"]}

    def test_list_architectures_text(self, mock_discovery, capsys) -> None:  # noqa: PLR6301
        """Test listing architectures in text format."""
        mock_discovery.find_release_file.return_value = "https://example.com/Release"
        mock_discovery.get_architectures.return_value = ["amd64", "arm64"]

        ArchitectureLister.list_architectures("https://example.com", "jammy", OutputFormat.TEXT)

        captured = capsys.readouterr()
        assert "Available architectures:" in captured.out
        assert "amd64" in captured.out
        assert "arm64" in captured.out

    def test_list_architectures_no_release_exits(self, mock_discovery) -> None:  # noqa: PLR6301
        """Test that missing release file causes exit."""
        mock_discovery.find_release_file.return_value = None

        with pytest.raises(SystemExit):
            ArchitectureLister.list_architectures("https://example.com", "jammy", OutputFormat.JSON)


# ===== PackageQuerier Tests =====


class TestPackageQuerier:
    """Test PackageQuerier class."""

    def test_query_packages_json(self, mock_package_index, sample_packages, capsys) -> None:  # noqa: PLR6301
        """Test querying packages in JSON format."""
        mock_package_index.get_all_packages.return_value = sample_packages
        mock_package_index.filter_by_name.return_value = [sample_packages[0]]

        PackageQuerier.query_packages(
            "https://example.com", "amd64", "main", "nginx", None, None, OutputFormat.JSON
        )

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert len(output) == 1
        assert output[0]["package"] == "nginx"

    def test_query_packages_text(self, mock_package_index, sample_packages, capsys) -> None:  # noqa: PLR6301
        """Test querying packages in text format."""
        mock_package_index.get_all_packages.return_value = sample_packages[:1]

        PackageQuerier.query_packages(
            "https://example.com", "amd64", "main", None, None, None, OutputFormat.TEXT
        )

        captured = capsys.readouterr()
        assert "Package: nginx" in captured.out
        assert "Version: 1.18.0-0ubuntu1" in captured.out
        assert "Architecture: amd64" in captured.out

    def test_query_with_regex_filter(self, mock_package_index, sample_packages) -> None:  # noqa: PLR6301
        """Test querying with regex filter."""
        python_packages = [p for p in sample_packages if p.package.startswith("python")]
        mock_package_index.get_all_packages.return_value = sample_packages
        mock_package_index.filter_by_regex.return_value = python_packages

        PackageQuerier.query_packages(
            "https://example.com", "amd64", "main", None, "^python.*", None, OutputFormat.JSON
        )

        mock_package_index.filter_by_regex.assert_called_once_with("^python.*")

    def test_query_with_version_filter(self, mock_package_index, sample_packages) -> None:  # noqa: PLR6301
        """Test querying with version filter."""
        mock_package_index.get_all_packages.return_value = sample_packages
        mock_package_index.filter_by_version.return_value = sample_packages[:1]

        PackageQuerier.query_packages(
            "https://example.com", "amd64", "main", None, None, ">=1.0", OutputFormat.JSON
        )

        mock_package_index.filter_by_version.assert_called_once_with(">=1.0")

    def test_query_with_multiple_filters(self, mock_package_index, sample_packages) -> None:  # noqa: PLR6301
        """Test querying with multiple filters applied."""
        mock_package_index.get_all_packages.return_value = sample_packages
        mock_package_index.filter_by_name.return_value = [sample_packages[0]]
        mock_package_index.filter_by_regex.return_value = [sample_packages[0]]
        mock_package_index.filter_by_version.return_value = [sample_packages[0]]

        PackageQuerier.query_packages(
            "https://example.com", "amd64", "main", "nginx", "^ng.*", ">=1.0", OutputFormat.JSON
        )

        # Verify all filters were applied
        mock_package_index.filter_by_name.assert_called_once_with("nginx")
        mock_package_index.filter_by_regex.assert_called_once()
        mock_package_index.filter_by_version.assert_called_once()


# ===== RepositoryExplorer Tests =====


class TestRepositoryExplorer:
    """Test RepositoryExplorer class."""

    def test_explorer_initialization(self) -> None:  # noqa: PLR6301
        """Test RepositoryExplorer initialization."""
        with patch("apt_registry_explorer.cli.RepositoryDiscovery"):
            explorer = RepositoryExplorer("https://example.com", SourcesFormat.DEB822)
            assert explorer.url == "https://example.com"
            assert explorer.output_format == SourcesFormat.DEB822

    def test_explore_empty_directory(self, mock_discovery, capsys) -> None:  # noqa: PLR6301
        """Test exploring empty directory."""
        with patch("apt_registry_explorer.cli.RepositoryDiscovery") as mock_cls:
            mock_cls.return_value = mock_discovery
            mock_discovery.list_directory.return_value = []

            explorer = RepositoryExplorer("https://example.com", SourcesFormat.DEB822)
            explorer.explore()

            captured = capsys.readouterr()
            assert "No items found at URL" in captured.out

    def test_explore_with_dists_directory(self, mock_discovery, capsys) -> None:  # noqa: PLR6301
        """Test exploring repository with dists directory."""
        with patch("apt_registry_explorer.cli.RepositoryDiscovery") as mock_cls:
            mock_cls.return_value = mock_discovery
            # Mock directory listing
            mock_discovery.list_directory.side_effect = [
                [("dists", "dir"), ("pool", "dir")],  # Root listing
                [("jammy", "dir"), ("focal", "dir")],  # Dists listing
            ]
            mock_discovery.navigate.return_value = "https://example.com/dists"
            mock_discovery.find_release_file.return_value = (
                "https://example.com/dists/jammy/Release"
            )
            mock_discovery.get_architectures.return_value = ["amd64", "arm64"]
            mock_discovery.get_components.return_value = ["main", "universe"]

            explorer = RepositoryExplorer("https://example.com", SourcesFormat.DEB822)
            explorer.explore()

            captured = capsys.readouterr()
            assert "Exploring:" in captured.out
            assert "Available directories:" in captured.out
            assert "dists" in captured.out
            assert "Available suites:" in captured.out
            assert "jammy" in captured.out

    def test_explore_generates_deb822_config(self, mock_discovery, capsys) -> None:  # noqa: PLR6301
        """Test that explore generates deb822 format configuration."""
        with (
            patch("apt_registry_explorer.cli.RepositoryDiscovery") as mock_cls,
            patch("apt_registry_explorer.cli.SourcesBuilder") as mock_builder_cls,
        ):
            mock_cls.return_value = mock_discovery
            mock_builder = MagicMock()
            mock_builder_cls.return_value = mock_builder
            mock_builder.build_deb822.return_value = "Types: deb\nURIs: https://example.com"

            mock_discovery.list_directory.side_effect = [[("dists", "dir")], [("jammy", "dir")]]
            mock_discovery.navigate.return_value = "https://example.com/dists"
            mock_discovery.find_release_file.return_value = (
                "https://example.com/dists/jammy/Release"
            )
            mock_discovery.get_architectures.return_value = ["amd64"]
            mock_discovery.get_components.return_value = ["main"]

            explorer = RepositoryExplorer("https://example.com", SourcesFormat.DEB822)
            explorer.explore()

            captured = capsys.readouterr()
            assert "Generated sources configuration:" in captured.out

    def test_explore_generates_oneline_config(self, mock_discovery, capsys) -> None:  # noqa: PLR6301
        """Test that explore generates one-line format configuration."""
        with (
            patch("apt_registry_explorer.cli.RepositoryDiscovery") as mock_cls,
            patch("apt_registry_explorer.cli.SourcesBuilder") as mock_builder_cls,
        ):
            mock_cls.return_value = mock_discovery
            mock_builder = MagicMock()
            mock_builder_cls.return_value = mock_builder
            mock_builder.build_one_line.return_value = ["deb https://example.com jammy main"]

            mock_discovery.list_directory.side_effect = [[("dists", "dir")], [("jammy", "dir")]]
            mock_discovery.navigate.return_value = "https://example.com/dists"
            mock_discovery.find_release_file.return_value = (
                "https://example.com/dists/jammy/Release"
            )
            mock_discovery.get_architectures.return_value = ["amd64"]
            mock_discovery.get_components.return_value = ["main"]

            explorer = RepositoryExplorer("https://example.com", SourcesFormat.ONELINE)
            explorer.explore()

            captured = capsys.readouterr()
            assert "Generated sources configuration:" in captured.out


# ===== Integration Tests for CLI Commands =====


class TestCLICommands:
    """Integration tests for CLI commands using CliRunner."""

    def test_query_command_requires_arch(self) -> None:  # noqa: PLR6301
        """Test that query command requires --arch parameter."""
        runner = CliRunner()
        result = runner.invoke(app, ["query", "--source", "https://example.com"])
        assert result.exit_code == 1
        assert "--arch is required" in result.output

    def test_query_command_with_list_arch(self, mock_discovery) -> None:  # noqa: PLR6301
        """Test query command with --list-arch flag."""
        mock_discovery.find_release_file.return_value = "https://example.com/Release"
        mock_discovery.get_architectures.return_value = ["amd64", "arm64"]

        with patch("apt_registry_explorer.cli.RepositoryDiscovery") as mock_cls:
            mock_cls.return_value = mock_discovery
            runner = CliRunner()
            result = runner.invoke(app, ["query", "--source", "https://example.com", "--list-arch"])
            assert result.exit_code == 0
            assert "amd64" in result.output

    def test_discover_command(self, mock_discovery) -> None:  # noqa: PLR6301
        """Test discover command."""
        with patch("apt_registry_explorer.cli.RepositoryDiscovery") as mock_cls:
            mock_cls.return_value = mock_discovery
            mock_discovery.list_directory.return_value = [("dists", "dir")]

            runner = CliRunner()
            result = runner.invoke(app, ["discover", "https://example.com"])
            assert result.exit_code == 0
            assert "Exploring:" in result.output
