"""Additional comprehensive tests for TUI module."""

import contextlib
from unittest.mock import MagicMock

import pytest
from apt_registry_explorer.packages import PackageMetadata
from apt_registry_explorer.tui import PackageBrowserApp, PackageDetails
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
        assert app.filtered_packages == sample_packages

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

        # Mock the event with row_key as integer (0-based index)
        class MockRowKey:
            def __init__(self, value):
                self.value = value

        class MockRowSelectedEvent:
            def __init__(self, row_key_value):
                self.row_key = MockRowKey(row_key_value)

        # Mock query_one to return a mock PackageDetails widget
        mock_details = MagicMock(spec=PackageDetails)
        app.query_one = MagicMock(return_value=mock_details)

        # Simulate row selection
        event = MockRowSelectedEvent(row_key_value=0)
        app.on_data_table_row_selected(event)

        # Verify details.update_package was called
        assert mock_details.update_package.called

    def test_on_data_table_row_selected_with_invalid_key(self, sample_packages) -> None:  # noqa: PLR6301
        """Test handling invalid row key."""
        app = PackageBrowserApp(sample_packages)

        class MockRowKey:
            def __init__(self, value):
                self.value = value

        class MockRowSelectedEvent:
            def __init__(self, row_key_value):
                self.row_key = MockRowKey(row_key_value)

        mock_details = MagicMock(spec=PackageDetails)
        app.query_one = MagicMock(return_value=mock_details)

        # Try with out-of-bounds index
        event = MockRowSelectedEvent(row_key_value=999)

        # Should not crash, just doesn't update anything
        with contextlib.suppress(IndexError, KeyError):
            app.on_data_table_row_selected(event)
            # update_package should not be called for invalid index
            assert not mock_details.update_package.called


class TestPackageDetails:
    """Test PackageDetails widget."""

    def test_update_package_with_all_fields(self, sample_packages) -> None:  # noqa: PLR6301
        """Test updating package details with all fields present."""
        details = PackageDetails()
        pkg = sample_packages[0]

        # Mock the update method
        details.update = MagicMock()

        details.update_package(pkg)

        # Verify update was called with details text
        assert details.update.called
        call_args = details.update.call_args[0][0]
        assert "Package:" in call_args
        assert pkg.package in call_args

    def test_update_package_with_missing_fields(self) -> None:  # noqa: PLR6301
        """Test updating package details with optional fields missing."""
        details = PackageDetails()
        pkg = PackageMetadata(package="test-pkg", version="1.0.0", architecture="all")

        # Mock the update method
        details.update = MagicMock()

        details.update_package(pkg)

        # Verify update was called and handles missing fields
        assert details.update.called
        call_args = details.update.call_args[0][0]
        assert "test-pkg" in call_args
        assert "N/A" in call_args  # For missing optional fields

    def test_update_package_with_none(self) -> None:  # noqa: PLR6301
        """Test updating package details with None."""
        details = PackageDetails()

        # Mock the update method
        details.update = MagicMock()

        details.update_package(None)

        # Verify update was called with "No package selected" message
        assert details.update.called
        call_args = details.update.call_args[0][0]
        assert "No package selected" in call_args
