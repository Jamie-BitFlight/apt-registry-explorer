"""
Package metadata parsing and querying module.
"""

import gzip
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests


@dataclass
class PackageMetadata:
    """Package metadata similar to apt-cache output."""

    package: str
    version: str
    architecture: str
    maintainer: Optional[str] = None
    installed_size: Optional[str] = None
    depends: Optional[str] = None
    recommends: Optional[str] = None
    suggests: Optional[str] = None
    conflicts: Optional[str] = None
    replaces: Optional[str] = None
    provides: Optional[str] = None
    section: Optional[str] = None
    priority: Optional[str] = None
    homepage: Optional[str] = None
    description: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[str] = None
    md5sum: Optional[str] = None
    sha1: Optional[str] = None
    sha256: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class PackageIndex:
    """Parse and query package index (Packages file)."""

    def __init__(self, timeout: int = 10):
        """
        Initialize package index.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "apt-registry-explorer/1.0"})
        self.packages: List[PackageMetadata] = []

    def fetch_packages_file(self, url: str, architecture: str, component: str) -> str:
        """
        Fetch Packages file from repository.

        Args:
            url: Base URL of repository
            architecture: Architecture (e.g., amd64)
            component: Component (e.g., main)

        Returns:
            Content of Packages file
        """
        # Try compressed version first
        packages_gz_url = urljoin(
            url, f"dists/stable/{component}/binary-{architecture}/Packages.gz"
        )
        
        try:
            response = self.session.get(packages_gz_url, timeout=self.timeout)
            response.raise_for_status()
            content = gzip.decompress(response.content).decode("utf-8")
            return content
        except requests.RequestException:
            pass
        
        # Try uncompressed version
        packages_url = urljoin(
            url, f"dists/stable/{component}/binary-{architecture}/Packages"
        )
        
        try:
            response = self.session.get(packages_url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch Packages file: {e}")

    def parse_packages_file(self, content: str) -> List[PackageMetadata]:
        """
        Parse Packages file content.

        Args:
            content: Content of Packages file

        Returns:
            List of package metadata
        """
        packages = []
        current_package = {}
        current_field = None
        
        for line in content.split("\n"):
            # Empty line separates packages
            if not line.strip():
                if current_package:
                    packages.append(self._create_package_metadata(current_package))
                    current_package = {}
                    current_field = None
                continue
            
            # Continuation line (starts with space)
            if line.startswith(" ") and current_field:
                current_package[current_field] += "\n" + line.strip()
                continue
            
            # New field
            if ":" in line:
                field, value = line.split(":", 1)
                field = field.strip()
                value = value.strip()
                current_package[field] = value
                current_field = field
        
        # Add last package if exists
        if current_package:
            packages.append(self._create_package_metadata(current_package))
        
        return packages

    def _create_package_metadata(self, pkg_dict: Dict[str, str]) -> PackageMetadata:
        """Create PackageMetadata from dictionary."""
        return PackageMetadata(
            package=pkg_dict.get("Package", ""),
            version=pkg_dict.get("Version", ""),
            architecture=pkg_dict.get("Architecture", ""),
            maintainer=pkg_dict.get("Maintainer"),
            installed_size=pkg_dict.get("Installed-Size"),
            depends=pkg_dict.get("Depends"),
            recommends=pkg_dict.get("Recommends"),
            suggests=pkg_dict.get("Suggests"),
            conflicts=pkg_dict.get("Conflicts"),
            replaces=pkg_dict.get("Replaces"),
            provides=pkg_dict.get("Provides"),
            section=pkg_dict.get("Section"),
            priority=pkg_dict.get("Priority"),
            homepage=pkg_dict.get("Homepage"),
            description=pkg_dict.get("Description"),
            filename=pkg_dict.get("Filename"),
            size=pkg_dict.get("Size"),
            md5sum=pkg_dict.get("MD5sum"),
            sha1=pkg_dict.get("SHA1"),
            sha256=pkg_dict.get("SHA256"),
        )

    def load_from_url(self, url: str, architecture: str, component: str = "main"):
        """
        Load packages from repository URL.

        Args:
            url: Repository URL
            architecture: Architecture to load
            component: Component to load
        """
        content = self.fetch_packages_file(url, architecture, component)
        self.packages = self.parse_packages_file(content)

    def filter_by_name(self, name: str) -> List[PackageMetadata]:
        """Filter packages by exact name match."""
        return [pkg for pkg in self.packages if pkg.package == name]

    def filter_by_regex(self, pattern: str) -> List[PackageMetadata]:
        """Filter packages by regex pattern."""
        regex = re.compile(pattern)
        return [pkg for pkg in self.packages if regex.search(pkg.package)]

    def filter_by_version(self, version_spec: str) -> List[PackageMetadata]:
        """
        Filter packages by version specification.

        Args:
            version_spec: Version specification (e.g., '>=1.0', '==2.0')

        Returns:
            Filtered packages
        """
        # Simple version comparison (can be enhanced with packaging library)
        if version_spec.startswith(">="):
            target = version_spec[2:].strip()
            return [pkg for pkg in self.packages if pkg.version >= target]
        elif version_spec.startswith("<="):
            target = version_spec[2:].strip()
            return [pkg for pkg in self.packages if pkg.version <= target]
        elif version_spec.startswith("=="):
            target = version_spec[2:].strip()
            return [pkg for pkg in self.packages if pkg.version == target]
        elif version_spec.startswith(">"):
            target = version_spec[1:].strip()
            return [pkg for pkg in self.packages if pkg.version > target]
        elif version_spec.startswith("<"):
            target = version_spec[1:].strip()
            return [pkg for pkg in self.packages if pkg.version < target]
        else:
            return [pkg for pkg in self.packages if pkg.version == version_spec]

    def get_all_packages(self) -> List[PackageMetadata]:
        """Get all loaded packages."""
        return self.packages
