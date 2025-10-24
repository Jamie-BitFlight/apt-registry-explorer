"""
CLI module for command-line operations.
"""

import json
import sys
from typing import Optional

import click

from .discovery import RepositoryDiscovery
from .packages import PackageIndex
from .sources import SourceOptions, SourcesBuilder


@click.group()
@click.version_option()
def main():
    """apt-registry-explorer - Explore APT repositories without root access."""
    pass


@main.command()
@click.option("--source", required=True, help="Repository URL or deb line")
@click.option("--list-arch", is_flag=True, help="List available architectures")
@click.option("--arch", help="Architecture to query (e.g., amd64)")
@click.option("--package", help="Package name to search")
@click.option("--version", "version_spec", help="Version specification (e.g., >=1.0)")
@click.option("--regex", help="Regex pattern to match package names")
@click.option("--component", default="main", help="Component to query (default: main)")
@click.option("--output", type=click.Choice(["json", "text"]), default="json", help="Output format")
def query(
    source: str,
    list_arch: bool,
    arch: Optional[str],
    package: Optional[str],
    version_spec: Optional[str],
    regex: Optional[str],
    component: str,
    output: str,
):
    """Query APT repository for package information."""
    try:
        # Parse source
        if source.startswith("deb "):
            # Parse deb line
            builder = SourcesBuilder()
            parsed = builder.parse_deb_line(source)
            if not parsed:
                click.echo("Error: Invalid deb line", err=True)
                sys.exit(1)
            repo_url = parsed["url"]
            suite = parsed["suite"]
        else:
            # Assume URL
            repo_url = source
            suite = "stable"
        
        # List architectures if requested
        if list_arch:
            discovery = RepositoryDiscovery(repo_url)
            release_url = discovery.find_release_file(repo_url.rstrip("/") + f"/dists/{suite}/")
            if release_url:
                architectures = discovery.get_architectures(release_url)
                if output == "json":
                    click.echo(json.dumps({"architectures": architectures}, indent=2))
                else:
                    click.echo("Available architectures:")
                    for arch_item in architectures:
                        click.echo(f"  - {arch_item}")
            else:
                click.echo("Error: Could not find Release file", err=True)
                sys.exit(1)
            return
        
        # Query packages
        if not arch:
            click.echo("Error: --arch is required for package queries", err=True)
            sys.exit(1)
        
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
        if output == "json":
            result = [pkg.to_dict() for pkg in packages]
            click.echo(json.dumps(result, indent=2))
        else:
            for pkg in packages:
                click.echo(f"Package: {pkg.package}")
                click.echo(f"Version: {pkg.version}")
                click.echo(f"Architecture: {pkg.architecture}")
                if pkg.description:
                    click.echo(f"Description: {pkg.description}")
                click.echo()
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("url")
@click.option("--format", type=click.Choice(["deb822", "oneline"]), default="deb822", help="Output format")
def discover(url: str, format: str):
    """Interactively discover repository structure and generate sources configuration."""
    try:
        discovery = RepositoryDiscovery(url)
        
        # List initial directory
        click.echo(f"Exploring: {url}")
        items = discovery.list_directory(url)
        
        if not items:
            click.echo("No items found at URL")
            return
        
        # Display items
        click.echo("\nAvailable directories:")
        for name, item_type in items:
            if item_type == "dir":
                click.echo(f"  [DIR]  {name}")
        
        # Look for common distribution directories
        common_dists = ["dists", "debian", "ubuntu"]
        dists_dir = None
        
        for name, item_type in items:
            if item_type == "dir" and name in common_dists:
                dists_dir = name
                break
        
        if dists_dir:
            click.echo(f"\nFound distributions directory: {dists_dir}")
            dists_url = discovery.navigate([dists_dir])
            
            # List suites
            suites = discovery.list_directory(dists_url)
            click.echo("\nAvailable suites:")
            for name, item_type in suites:
                if item_type == "dir":
                    click.echo(f"  - {name}")
                    
                    # Try to find Release file
                    suite_url = discovery.navigate([dists_dir, name])
                    release_url = discovery.find_release_file(suite_url)
                    
                    if release_url:
                        archs = discovery.get_architectures(release_url)
                        comps = discovery.get_components(release_url)
                        
                        if archs or comps:
                            click.echo(f"    Architectures: {', '.join(archs)}")
                            click.echo(f"    Components: {', '.join(comps)}")
                            
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
                            
                            click.echo("\n    Generated sources configuration:")
                            if format == "deb822":
                                click.echo("    " + builder.build_deb822().replace("\n", "\n    "))
                            else:
                                for line in builder.build_one_line():
                                    click.echo(f"    {line}")
                            click.echo()
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
