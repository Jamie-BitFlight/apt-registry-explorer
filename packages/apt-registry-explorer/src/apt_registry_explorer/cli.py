"""CLI module for command-line operations."""

import json
from enum import StrEnum
from typing import Annotated

import typer

from .discovery import RepositoryDiscovery
from .packages import PackageIndex, PackageMetadata
from .sources import SourceOptions, SourcesBuilder

app = typer.Typer(
    name="apt-registry-explorer",
    help="Explore APT repositories without root access",
    add_completion=False,
)


class OutputFormat(StrEnum):
    """Output format options."""

    JSON = "json"
    TEXT = "text"


class SourcesFormat(StrEnum):
    """Sources file format options."""

    DEB822 = "deb822"
    ONELINE = "oneline"


class SourceParser:
    """Parse different source input formats."""

    @staticmethod
    def parse_source(source: str) -> tuple[str, str]:
        """Parse source input and extract URL and suite.

        Args:
            source: Either a deb line or a URL

        Returns:
            Tuple of (url, suite)

        Raises:
            typer.Exit: If the source is invalid

        """
        if source.startswith("deb "):
            return SourceParser._parse_deb_line(source)
        return source, "stable"

    @staticmethod
    def _parse_deb_line(source: str) -> tuple[str, str]:
        """Parse deb line format."""
        builder = SourcesBuilder()
        if not (parsed := builder.parse_deb_line(source)):
            typer.echo("Error: Invalid deb line", err=True)
            raise typer.Exit(1)

        parsed_url = parsed["url"]
        parsed_suite = parsed["suite"]

        # Type narrowing: if parse succeeded, url and suite are strings
        repo_url = parsed_url if isinstance(parsed_url, str) else parsed_url[0]
        suite = parsed_suite if isinstance(parsed_suite, str) else parsed_suite[0]

        return repo_url, suite


class ArchitectureLister:
    """List available architectures from a repository."""

    @staticmethod
    def list_architectures(repo_url: str, suite: str, output: OutputFormat) -> None:
        """List architectures and output them.

        Args:
            repo_url: Repository URL
            suite: Distribution suite
            output: Output format

        Raises:
            typer.Exit: If release file not found

        """
        discovery = RepositoryDiscovery(repo_url)
        release_url = discovery.find_release_file(f"{repo_url.rstrip('/')}/dists/{suite}/")

        if not release_url:
            typer.echo("Error: Could not find Release file", err=True)
            raise typer.Exit(1)

        architectures = discovery.get_architectures(release_url)
        ArchitectureLister._output_architectures(architectures, output)

    @staticmethod
    def _output_architectures(architectures: list[str], output: OutputFormat) -> None:
        """Output architectures in the requested format."""
        match output:
            case OutputFormat.JSON:
                typer.echo(json.dumps({"architectures": architectures}, indent=2))
            case OutputFormat.TEXT:
                typer.echo("Available architectures:")
                for arch_item in architectures:
                    typer.echo(f"  - {arch_item}")


class PackageQuerier:
    """Query and filter packages from a repository."""

    @staticmethod
    def query_packages(
        repo_url: str,
        arch: str,
        component: str,
        package: str | None,
        regex: str | None,
        version_spec: str | None,
        output: OutputFormat,
    ) -> None:
        """Query packages with filters and output results.

        Args:
            repo_url: Repository URL
            arch: Architecture to query
            component: Component to query
            package: Package name filter
            regex: Regex pattern filter
            version_spec: Version specification filter
            output: Output format

        """
        index = PackageIndex()
        index.load_from_url(repo_url, arch, component)

        packages = PackageQuerier._apply_filters(index, package, regex, version_spec)
        PackageQuerier._output_packages(packages, output)

    @staticmethod
    def _apply_filters(
        index: PackageIndex, package: str | None, regex: str | None, version_spec: str | None
    ) -> list[PackageMetadata]:
        """Apply filters to package index."""
        packages = index.get_all_packages()

        if package:
            packages = index.filter_by_name(package)

        if regex:
            index.packages = packages
            packages = index.filter_by_regex(regex)

        if version_spec:
            index.packages = packages
            packages = index.filter_by_version(version_spec)

        return packages

    @staticmethod
    def _output_packages(packages: list[PackageMetadata], output: OutputFormat) -> None:
        """Output packages in the requested format."""
        match output:
            case OutputFormat.JSON:
                result = [pkg.to_dict() for pkg in packages]
                typer.echo(json.dumps(result, indent=2))
            case OutputFormat.TEXT:
                for pkg in packages:
                    typer.echo(f"Package: {pkg.package}")
                    typer.echo(f"Version: {pkg.version}")
                    typer.echo(f"Architecture: {pkg.architecture}")
                    if pkg.description:
                        typer.echo(f"Description: {pkg.description}")
                    typer.echo()


@app.command()
def query(
    source: Annotated[str, typer.Option(help="Repository URL or deb line")],
    list_arch: Annotated[
        bool, typer.Option("--list-arch", help="List available architectures")
    ] = False,
    arch: Annotated[str | None, typer.Option(help="Architecture to query (e.g., amd64)")] = None,
    package: Annotated[str | None, typer.Option(help="Package name to search")] = None,
    version_spec: Annotated[
        str | None, typer.Option("--version", help="Version specification (e.g., >=1.0)")
    ] = None,
    regex: Annotated[str | None, typer.Option(help="Regex pattern to match package names")] = None,
    component: Annotated[str, typer.Option(help="Component to query")] = "main",
    output: Annotated[OutputFormat, typer.Option(help="Output format")] = OutputFormat.JSON,
) -> None:
    """Query APT repository for package information."""
    repo_url, suite = SourceParser.parse_source(source)

    if list_arch:
        ArchitectureLister.list_architectures(repo_url, suite, output)
        return

    if not arch:
        typer.echo("Error: --arch is required for package queries", err=True)
        raise typer.Exit(1)

    PackageQuerier.query_packages(repo_url, arch, component, package, regex, version_spec, output)


class RepositoryExplorer:
    """Explore repository structure and generate sources configuration."""

    def __init__(self, url: str, output_format: SourcesFormat) -> None:
        """Initialize explorer.

        Args:
            url: Repository URL
            output_format: Output format for sources configuration

        """
        self.url = url
        self.output_format = output_format
        self.discovery = RepositoryDiscovery(url)

    def explore(self) -> None:
        """Explore repository and display information."""
        typer.echo(f"Exploring: {self.url}")

        items = self.discovery.list_directory(self.url)
        if not items:
            typer.echo("No items found at URL")
            return

        self._display_directory_items(items)
        self._explore_distributions(items)

    @staticmethod
    def _display_directory_items(items: list[tuple[str, str]]) -> None:
        """Display directory items."""
        typer.echo("\nAvailable directories:")
        for name, item_type in items:
            if item_type == "dir":
                typer.echo(f"  [DIR]  {name}")

    def _explore_distributions(self, items: list[tuple[str, str]]) -> None:
        """Find and explore distribution directories."""
        dists_dir = self._find_distributions_dir(items)

        if not dists_dir:
            return

        typer.echo(f"\nFound distributions directory: {dists_dir}")
        dists_url = self.discovery.navigate([dists_dir])

        suites = self.discovery.list_directory(dists_url)
        self._explore_suites(dists_dir, suites)

    @staticmethod
    def _find_distributions_dir(items: list[tuple[str, str]]) -> str | None:
        """Find common distribution directory."""
        common_dists = ["dists", "debian", "ubuntu"]

        for name, item_type in items:
            if item_type == "dir" and name in common_dists:
                return name

        return None

    def _explore_suites(self, dists_dir: str, suites: list[tuple[str, str]]) -> None:
        """Explore suites in distributions directory."""
        typer.echo("\nAvailable suites:")

        for name, item_type in suites:
            if item_type == "dir":
                self._explore_suite(dists_dir, name)

    def _explore_suite(self, dists_dir: str, suite_name: str) -> None:
        """Explore a single suite."""
        typer.echo(f"  - {suite_name}")

        suite_url = self.discovery.navigate([dists_dir, suite_name])
        release_url = self.discovery.find_release_file(suite_url)

        if not release_url:
            return

        archs = self.discovery.get_architectures(release_url)
        comps = self.discovery.get_components(release_url)

        if archs or comps:
            typer.echo(f"    Architectures: {', '.join(archs)}")
            typer.echo(f"    Components: {', '.join(comps)}")
            self._generate_sources_config(suite_name, archs, comps)

    def _generate_sources_config(self, suite_name: str, archs: list[str], comps: list[str]) -> None:
        """Generate and display sources configuration."""
        builder = SourcesBuilder()
        options = SourceOptions(architectures=archs[:1] if archs else None)
        builder.add_source("deb", self.url, suite_name, comps or ["main"], options)

        typer.echo("\n    Generated sources configuration:")

        match self.output_format:
            case SourcesFormat.DEB822:
                config = builder.build_deb822()
                typer.echo("    " + config.replace("\n", "\n    "))
            case SourcesFormat.ONELINE:
                for line in builder.build_one_line():
                    typer.echo(f"    {line}")

        typer.echo()


@app.command()
def discover(
    url: Annotated[str, typer.Argument(help="Repository URL to explore")],
    output_format: Annotated[
        SourcesFormat, typer.Option("--format", help="Output format")
    ] = SourcesFormat.DEB822,
) -> None:
    """Interactively discover repository structure and generate sources configuration."""
    explorer = RepositoryExplorer(url, output_format)
    explorer.explore()


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
