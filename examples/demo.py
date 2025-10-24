#!/usr/bin/env python3
"""
Example script demonstrating the apt-registry-explorer functionality.
"""

import json
from apt_registry_explorer.discovery import RepositoryDiscovery
from apt_registry_explorer.packages import PackageIndex
from apt_registry_explorer.sources import SourceOptions, SourcesBuilder


def example_discovery():
    """Example of using the discovery module."""
    print("=== Discovery Example ===")
    print("This would explore a real APT repository")
    
    # This is a demonstration - would need a real repository
    discovery = RepositoryDiscovery("https://example.com/debian")
    print(f"Base URL: {discovery.base_url}")
    
    # Navigate to a path
    url = discovery.navigate(["dists", "stable"])
    print(f"Navigated URL: {url}")
    print()


def example_sources_builder():
    """Example of building APT sources configuration."""
    print("=== Sources Builder Example ===")
    
    builder = SourcesBuilder()
    
    # Add a source with options
    options = SourceOptions(
        architectures=["amd64", "arm64"],
        signed_by="/usr/share/keyrings/example.gpg"
    )
    
    builder.add_source(
        "deb",
        "https://example.com/debian",
        "stable",
        ["main", "contrib"],
        options
    )
    
    # Build deb822 format
    print("deb822 format:")
    print(builder.build_deb822())
    print()
    
    # Build one-line format
    print("One-line format:")
    for line in builder.build_one_line():
        print(line)
    print()


def example_parse_deb_line():
    """Example of parsing a deb line."""
    print("=== Parse Deb Line Example ===")
    
    builder = SourcesBuilder()
    line = "deb [arch=amd64 signed-by=/usr/share/keyrings/test.gpg] https://example.com/debian stable main contrib"
    
    parsed = builder.parse_deb_line(line)
    print(f"Original line: {line}")
    print(f"Parsed:")
    print(json.dumps(
        {k: v for k, v in parsed.items() if k != "options"},
        indent=2
    ))
    print(f"Options:")
    print(f"  - Architectures: {parsed['options'].architectures}")
    print(f"  - Signed-by: {parsed['options'].signed_by}")
    print()


def example_package_metadata():
    """Example of working with package metadata."""
    print("=== Package Metadata Example ===")
    
    # Example Packages file content
    packages_content = """Package: nginx
Version: 1.24.0-1
Architecture: amd64
Maintainer: Debian Nginx Maintainers <pkg-nginx-maintainers@lists.alioth.debian.org>
Installed-Size: 1024
Depends: libc6 (>= 2.34), libssl3 (>= 3.0.0)
Section: httpd
Priority: optional
Homepage: https://nginx.org
Description: small, powerful, scalable web/proxy server
 Nginx is a web server focusing on high concurrency, performance
 and low memory usage.

Package: python3
Version: 3.11.2-1
Architecture: amd64
Section: python
Priority: important
Description: interactive high-level object-oriented language
 Python is a high-level, interpreted, interactive, object-oriented
 programming language.

"""
    
    index = PackageIndex()
    packages = index.parse_packages_file(packages_content)
    
    print(f"Parsed {len(packages)} packages:")
    for pkg in packages:
        print(f"\n  Package: {pkg.package}")
        print(f"  Version: {pkg.version}")
        print(f"  Architecture: {pkg.architecture}")
        if pkg.description:
            desc_first_line = pkg.description.split('\n')[0]
            print(f"  Description: {desc_first_line}")
    
    # Filter by name
    print("\nFiltering by name 'nginx':")
    index.packages = packages
    filtered = index.filter_by_name("nginx")
    for pkg in filtered:
        print(f"  - {pkg.package} {pkg.version}")
    
    # Filter by regex
    print("\nFiltering by regex '^python':")
    filtered = index.filter_by_regex("^python")
    for pkg in filtered:
        print(f"  - {pkg.package} {pkg.version}")
    print()


def main():
    """Run all examples."""
    print("APT Registry Explorer Examples")
    print("=" * 60)
    print()
    
    example_discovery()
    example_sources_builder()
    example_parse_deb_line()
    example_package_metadata()
    
    print("=" * 60)
    print("Examples completed!")
    print("\nTo use the CLI:")
    print("  apt-registry-explorer query --source URL --arch amd64")
    print("  apt-registry-explorer discover URL")


if __name__ == "__main__":
    main()
