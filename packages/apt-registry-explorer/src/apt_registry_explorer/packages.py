"""Package metadata parsing and querying module."""

import gzip
import re
from typing import Any
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel


class PackageMetadata(BaseModel):
    """Package metadata similar to apt-cache output."""

    package: str
    version: str
    architecture: str
    maintainer: str | None = None
    installed_size: str | None = None
    depends: str | None = None
    recommends: str | None = None
    suggests: str | None = None
    conflicts: str | None = None
    replaces: str | None = None
    provides: str | None = None
    section: str | None = None
    priority: str | None = None
    homepage: str | None = None
    description: str | None = None
    filename: str | None = None
    size: str | None = None
    md5sum: str | None = None
    sha1: str | None = None
    sha256: str | None = None

    model_config = {"extra": "allow"}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(indent=2)


class PackageIndex:
    """Parse and query package index (Packages file)."""

    def __init__(self, timeout: int = 10) -> None:
        """Initialize package index.

        Args:
            timeout: Request timeout in seconds

        """
        self.timeout = timeout
        self.client = httpx.Client(
            timeout=timeout, headers={"User-Agent": "apt-registry-explorer/1.0"}
        )
        self.packages: list[PackageMetadata] = []

    async def fetch_packages_file_async(self, url: str, architecture: str, component: str) -> str:
        """Fetch Packages file from repository asynchronously.

        Args:
            url: Base URL of repository
            architecture: Architecture (e.g., amd64)
            component: Component (e.g., main)

        Returns:
            Content of Packages file

        """
        async with httpx.AsyncClient(
            timeout=self.timeout, headers={"User-Agent": "apt-registry-explorer/1.0"}
        ) as client:
            # Try compressed version first
            packages_gz_url = urljoin(
                url, f"dists/stable/{component}/binary-{architecture}/Packages.gz"
            )

            try:
                response = await client.get(packages_gz_url)
                response.raise_for_status()
                return gzip.decompress(response.content).decode("utf-8")
            except httpx.HTTPError:
                pass

            # Try uncompressed version
            packages_url = urljoin(url, f"dists/stable/{component}/binary-{architecture}/Packages")

            try:
                response = await client.get(packages_url)
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise ValueError(f"Failed to fetch Packages file: {e}") from e
            else:
                return response.text

    def fetch_packages_file(self, url: str, architecture: str, component: str) -> str:
        """Fetch Packages file from repository (sync version for backwards compatibility).

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
            response = self.client.get(packages_gz_url)
            response.raise_for_status()
            return gzip.decompress(response.content).decode("utf-8")
        except httpx.HTTPError:
            pass

        # Try uncompressed version
        packages_url = urljoin(url, f"dists/stable/{component}/binary-{architecture}/Packages")

        try:
            response = self.client.get(packages_url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch Packages file: {e}") from e
        else:
            return response.text

    def parse_packages_file(self, content: str) -> list[PackageMetadata]:
        """Parse Packages file content.

        Args:
            content: Content of Packages file

        Returns:
            List of package metadata

        """
        packages = []
        current_package: dict[str, str] = {}
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

    @staticmethod
    def _create_package_metadata(pkg_dict: dict[str, str]) -> PackageMetadata:
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

    def load_from_url(self, url: str, architecture: str, component: str = "main") -> None:
        """Load packages from repository URL.

        Args:
            url: Repository URL
            architecture: Architecture to load
            component: Component to load

        """
        content = self.fetch_packages_file(url, architecture, component)
        self.packages = self.parse_packages_file(content)

    def filter_by_name(self, name: str) -> list[PackageMetadata]:
        """Filter packages by exact name match."""
        return [pkg for pkg in self.packages if pkg.package == name]

    def filter_by_regex(self, pattern: str) -> list[PackageMetadata]:
        """Filter packages by regex pattern."""
        regex = re.compile(pattern)
        return [pkg for pkg in self.packages if regex.search(pkg.package)]

    def filter_by_version(self, version_spec: str) -> list[PackageMetadata]:
        """Filter packages by version specification.

        Args:
            version_spec: Version specification (e.g., '>=1.0', '==2.0')

        Returns:
            Filtered packages

        """
        # Simple version comparison (can be enhanced with packaging library)
        if version_spec.startswith(">="):
            target = version_spec[2:].strip()
            return [pkg for pkg in self.packages if pkg.version >= target]
        if version_spec.startswith("<="):
            target = version_spec[2:].strip()
            return [pkg for pkg in self.packages if pkg.version <= target]
        if version_spec.startswith("=="):
            target = version_spec[2:].strip()
            return [pkg for pkg in self.packages if pkg.version == target]
        if version_spec.startswith(">"):
            target = version_spec[1:].strip()
            return [pkg for pkg in self.packages if pkg.version > target]
        if version_spec.startswith("<"):
            target = version_spec[1:].strip()
            return [pkg for pkg in self.packages if pkg.version < target]
        return [pkg for pkg in self.packages if pkg.version == version_spec]

    def get_all_packages(self) -> list[PackageMetadata]:
        """Get all loaded packages."""
        return self.packages
