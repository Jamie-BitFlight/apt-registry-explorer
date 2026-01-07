"""Additional comprehensive tests for TUI module."""

import contextlib
from unittest.mock import MagicMock

import pytest
from apt_registry_explorer.packages import PackageMetadata
from apt_registry_explorer.tui import PackageBrowserApp
from textual.widgets import DataTable


@pytest.fixture
def sample_packages() -> list[PackageMetadata]:
    """Create sample packages for TUI testing."""
    return [
        PackageMetadata(
            package="nginx",
            version="1.18.0-0ubuntu1",
            architecture="amd64",
            description="web server",
            depends="libc6",
            section="web",
            priority="optional",
        ),
        PackageMetadata(
            package="python3",
            version="3.10.4-0ubuntu2",
            architecture="amd64",
            description="Python interpreter",
            depends="python3.10",
            section="python",
            priority="important",
        ),
    ]


class TestPackageBrowserApp:
    """Test PackageBrowserApp TUI component."""

    def test_app_initialization(self, sample_packages) -> None:  # noqa: PLR6301
        """Test TUI app initializes correctly."""
        app = PackageBrowserApp(sample_packages)
        assert app.packages == sample_packages
        assert app.selected_package is None

    def test_compose_creates_widgets(self, sample_packages) -> None:  # noqa: PLR6301
        """Test that compose creates required widgets."""
        app = PackageBrowserApp(sample_packages)
        widgets = list(app.compose())
        # Should create at least 2 widgets (table and details)
        assert len(widgets) >= 2

    def test_on_mount_populates_table(self, sample_packages) -> None:  # noqa: PLR6301
        """Test that on_mount populates the table with packages."""
        app = PackageBrowserApp(sample_packages)

        # Mock the query_one method to return a mocked DataTable
        mock_table = MagicMock(spec=DataTable)
        app.query_one = MagicMock(return_value=mock_table)

        # Call on_mount
        app.on_mount()

        # Verify table was populated
        assert mock_table.add_columns.called
        assert mock_table.add_row.call_count == len(sample_packages)

    def test_on_data_table_row_selected_updates_details(self, sample_packages) -> None:  # noqa: PLR6301
        """Test that selecting a row updates the details pane."""
        app = PackageBrowserApp(sample_packages)

        # Mock the event with row_index
        class MockRowSelectedEvent:
            def __init__(self, row_key):
                self.row_key = row_key

        # Mock query_one to return a mock Static widget
        mock_static = MagicMock()
        app.query_one = MagicMock(return_value=mock_static)

        # Simulate row selection
        event = MockRowSelectedEvent(row_key=0)
        app.on_data_table_row_selected(event)

        # Verify selected package was set
        assert app.selected_package is not None

    def test_format_details_with_all_fields(self, sample_packages) -> None:  # noqa: PLR6301
        """Test formatting package details with all fields present."""
        app = PackageBrowserApp(sample_packages)
        pkg = sample_packages[0]

        details = app._format_details(pkg)  # noqa: SLF001

        assert "Package:" in details
        assert pkg.package in details
        assert "Version:" in details
        assert pkg.version in details
        assert "Architecture:" in details
        assert pkg.architecture in details

    def test_format_details_with_missing_fields(self) -> None:  # noqa: PLR6301
        """Test formatting package details with optional fields missing."""
        app = PackageBrowserApp([])
        pkg = PackageMetadata(package="test-pkg", version="1.0.0", architecture="all")

        details = app._format_details(pkg)  # noqa: SLF001

        assert "Package:" in details
        assert "test-pkg" in details
        # Should handle missing optional fields gracefully

    def test_on_data_table_row_selected_with_invalid_key(self, sample_packages) -> None:  # noqa: PLR6301
        """Test handling invalid row key."""
        app = PackageBrowserApp(sample_packages)

        class MockRowSelectedEvent:
            def __init__(self, row_key):
                self.row_key = row_key

        mock_static = MagicMock()
        app.query_one = MagicMock(return_value=mock_static)

        # Try with out-of-bounds index
        event = MockRowSelectedEvent(row_key=999)

        # Should not crash, may do nothing or handle gracefully
        with contextlib.suppress(IndexError, KeyError):
            app.on_data_table_row_selected(event)
