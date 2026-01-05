"""
TUI module with fzf-style package browser.
"""

from rich.console import Console
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Input, Static

from .packages import PackageMetadata


class PackageDetails(Static):
    """Widget to display package details."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize package details widget."""
        super().__init__(*args, **kwargs)
        self.current_package: PackageMetadata | None = None

    def update_package(self, package: PackageMetadata | None) -> None:
        """Update displayed package information."""
        self.current_package = package
        if package:
            details = f"""[bold]Package:[/bold] {package.package}
[bold]Version:[/bold] {package.version}
[bold]Architecture:[/bold] {package.architecture}
[bold]Section:[/bold] {package.section or 'N/A'}
[bold]Priority:[/bold] {package.priority or 'N/A'}
[bold]Installed Size:[/bold] {package.installed_size or 'N/A'}

[bold]Maintainer:[/bold]
{package.maintainer or 'N/A'}

[bold]Depends:[/bold]
{package.depends or 'N/A'}

[bold]Description:[/bold]
{package.description or 'N/A'}

[bold]Homepage:[/bold] {package.homepage or 'N/A'}
[bold]Filename:[/bold] {package.filename or 'N/A'}
[bold]Size:[/bold] {package.size or 'N/A'}
"""
            self.update(details)
        else:
            self.update("[dim]No package selected[/dim]")


class PackageBrowserApp(App):
    """TUI application for browsing APT packages."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #search-container {
        height: 3;
        padding: 1;
    }

    #content-container {
        layout: horizontal;
        height: 1fr;
    }

    #packages-container {
        width: 50%;
        border: solid green;
    }

    #details-container {
        width: 50%;
        border: solid blue;
        padding: 1;
    }

    DataTable {
        height: 1fr;
    }

    Input {
        width: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("f", "focus_search", "Search"),
        ("/", "focus_search", "Search"),
    ]

    def __init__(self, packages: list[PackageMetadata], **kwargs) -> None:
        """
        Initialize package browser.

        Args:
            packages: List of packages to display
        """
        super().__init__(**kwargs)
        self.packages = packages
        self.filtered_packages = packages

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        
        with Container(id="search-container"):
            yield Input(placeholder="Search packages...", id="search-input")
        
        with Horizontal(id="content-container"):
            with Vertical(id="packages-container"):
                yield DataTable(id="packages-table")
            
            with Vertical(id="details-container"):
                yield PackageDetails(id="package-details")
        
        yield Footer()

    def on_mount(self) -> None:
        """Set up the application when mounted."""
        table = self.query_one("#packages-table", DataTable)
        table.add_columns("Package", "Version", "Architecture")
        
        # Populate table
        for pkg in self.packages:
            table.add_row(pkg.package, pkg.version, pkg.architecture)
        
        table.cursor_type = "row"
        table.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            search_term = event.value.lower()
            
            # Filter packages
            if search_term:
                self.filtered_packages = [
                    pkg for pkg in self.packages
                    if search_term in pkg.package.lower()
                ]
            else:
                self.filtered_packages = self.packages
            
            # Update table
            table = self.query_one("#packages-table", DataTable)
            table.clear()
            for pkg in self.filtered_packages:
                table.add_row(pkg.package, pkg.version, pkg.architecture)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in package table."""
        if event.row_key is not None:
            row_index = event.row_key.value
            if 0 <= row_index < len(self.filtered_packages):
                selected_package = self.filtered_packages[row_index]
                details = self.query_one("#package-details", PackageDetails)
                details.update_package(selected_package)

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()


def launch_tui(packages: list[PackageMetadata]) -> None:
    """
    Launch the TUI application.

    Args:
        packages: List of packages to display
    """
    app = PackageBrowserApp(packages)
    app.run()
