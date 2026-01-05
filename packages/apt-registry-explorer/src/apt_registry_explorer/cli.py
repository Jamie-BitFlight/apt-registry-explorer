"""
CLI module for command-line operations.
"""

import json
import sys
from enum import StrEnum
from typing import Annotated

import typer

from .discovery import RepositoryDiscovery
from .packages import PackageIndex
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


@app.command()
def query(
    source: Annotated[str, typer.Option(help="Repository URL or deb line")],
    list_arch: Annotated[bool, typer.Option("--list-arch", help="List available architectures")] = False,
    arch: Annotated[str | None, typer.Option(help="Architecture to query (e.g., amd64)")] = None,
    package: Annotated[str | None, typer.Option(help="Package name to search")] = None,
    version_spec: Annotated[str | None, typer.Option("--version", help="Version specification (e.g., >=1.0)")] = None,
    regex: Annotated[str | None, typer.Option(help="Regex pattern to match package names")] = None,
    component: Annotated[str, typer.Option(help="Component to query")] = "main",
    output: Annotated[OutputFormat, typer.Option(help="Output format")] = OutputFormat.JSON,
) -> None:
    """Query APT repository for package information."""
    try:
        # Parse source
        if source.startswith("deb "):
            # Parse deb line
            builder = SourcesBuilder()
            if not (parsed := builder.parse_deb_line(source)):
                typer.echo("Error: Invalid deb line", err=True)
                raise typer.Exit(1)
            repo_url = parsed["url"]
            suite = parsed["suite"]
        else:
            # Assume URL
            repo_url = source
            suite = "stable"
        
        # List architectures if requested
        if list_arch:
            discovery = RepositoryDiscovery(repo_url)
            if not (release_url := discovery.find_release_file(f"{repo_url.rstrip('/')}/dists/{suite}/")):
                typer.echo("Error: Could not find Release file", err=True)
                raise typer.Exit(1)
            
            architectures = discovery.get_architectures(release_url)
            match output:
                case OutputFormat.JSON:
                    typer.echo(json.dumps({"architectures": architectures}, indent=2))
                case OutputFormat.TEXT:
                    typer.echo("Available architectures:")
                    for arch_item in architectures:
                        typer.echo(f"  - {arch_item}")
            return
        
        # Query packages
        if not arch:
            typer.echo("Error: --arch is required for package queries", err=True)
            raise typer.Exit(1)
        
        index = PackageIndex()
        index.load_from_url(repo_url, arch, component)
        
        # Filter packages
        packages = index.get_all_packages()
        
        if package:
            packages = index.filter_by_name(package)
        
        if regex:
            index.packages = packages
            packages = index.filter_by_regex(regex)
        
        if version_spec:
            index.packages = packages
            packages = index.filter_by_version(version_spec)
        
        # Output results
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
    
    except (ValueError, KeyError, OSError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def discover(
    url: Annotated[str, typer.Argument(help="Repository URL to explore")],
    format: Annotated[SourcesFormat, typer.Option(help="Output format")] = SourcesFormat.DEB822,
) -> None:
    """Interactively discover repository structure and generate sources configuration."""
    try:
        discovery = RepositoryDiscovery(url)
        
        # List initial directory
        typer.echo(f"Exploring: {url}")
        items = discovery.list_directory(url)
        
        if not items:
            typer.echo("No items found at URL")
            return
        
        # Display items
        typer.echo("\nAvailable directories:")
        for name, item_type in items:
            if item_type == "dir":
                typer.echo(f"  [DIR]  {name}")
        
        # Look for common distribution directories
        common_dists = ["dists", "debian", "ubuntu"]
        dists_dir = None
        
        for name, item_type in items:
            if item_type == "dir" and name in common_dists:
                dists_dir = name
                break
        
        if dists_dir:
            typer.echo(f"\nFound distributions directory: {dists_dir}")
            dists_url = discovery.navigate([dists_dir])
            
            # List suites
            suites = discovery.list_directory(dists_url)
            typer.echo("\nAvailable suites:")
            for name, item_type in suites:
                if item_type == "dir":
                    typer.echo(f"  - {name}")
                    
                    # Try to find Release file
                    suite_url = discovery.navigate([dists_dir, name])
                    if not (release_url := discovery.find_release_file(suite_url)):
                        continue
                    
                    archs = discovery.get_architectures(release_url)
                    comps = discovery.get_components(release_url)
                    
                    if archs or comps:
                        typer.echo(f"    Architectures: {', '.join(archs)}")
                        typer.echo(f"    Components: {', '.join(comps)}")
                        
                        # Generate sources configuration
                        builder = SourcesBuilder()
                        options = SourceOptions(architectures=archs[:1] if archs else None)
                        builder.add_source(
                            "deb",
                            url,
                            name,
                            comps if comps else ["main"],
                            options
                        )
                        
                        typer.echo("\n    Generated sources configuration:")
                        match format:
                            case SourcesFormat.DEB822:
                                typer.echo("    " + builder.build_deb822().replace("\n", "\n    "))
                            case SourcesFormat.ONELINE:
                                for line in builder.build_one_line():
                                    typer.echo(f"    {line}")
                        typer.echo()
    
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
