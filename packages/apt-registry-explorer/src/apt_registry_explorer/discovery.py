"""
Interactive discovery module for navigating APT repository URLs.
"""

import re
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests


class RepositoryDiscovery:
    """Interactive discovery from partial URL to build apt.sources configuration."""

    def __init__(self, base_url: str, timeout: int = 10):
        """
        Initialize repository discovery.

        Args:
            base_url: Base URL of the APT repository (e.g., https://example.com/{os})
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "apt-registry-explorer/1.0"})

    def list_directory(self, url: str) -> List[Tuple[str, str]]:
        """
        List directories and files at a given URL.

        Args:
            url: URL to list

        Returns:
            List of tuples (name, type) where type is 'dir' or 'file'
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            content = response.text

            # Parse HTML directory listing (Apache/nginx style)
            items = []
            
            # Try to find links in HTML
            link_pattern = r'<a href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(link_pattern, content, re.IGNORECASE)
            
            for href, text in matches:
                # Skip parent directory and absolute URLs
                if href in ["../", "..", "/"]:
                    continue
                if href.startswith("http") or href.startswith("//"):
                    continue
                
                # Determine if it's a directory
                is_dir = href.endswith("/")
                item_name = href.rstrip("/")
                item_type = "dir" if is_dir else "file"
                
                if item_name:  # Skip empty names
                    items.append((item_name, item_type))
            
            return items
        except requests.RequestException as e:
            raise ValueError(f"Failed to list directory {url}: {e}")

    def navigate(self, path_components: List[str]) -> str:
        """
        Navigate to a specific path in the repository.

        Args:
            path_components: List of path components to navigate

        Returns:
            Final URL
        """
        url = self.base_url
        for component in path_components:
            if not url.endswith("/"):
                url += "/"
            url = urljoin(url, component + "/")
        return url

    def find_release_file(self, url: str) -> Optional[str]:
        """
        Find Release or InRelease file in a directory.

        Args:
            url: URL to search

        Returns:
            URL of Release/InRelease file if found
        """
        items = self.list_directory(url)
        
        for name, item_type in items:
            if item_type == "file" and name in ["InRelease", "Release", "Release.gpg"]:
                return urljoin(url, name)
        
        return None

    def get_architectures(self, release_url: str) -> List[str]:
        """
        Extract architectures from Release file.

        Args:
            release_url: URL of Release/InRelease file

        Returns:
            List of supported architectures
        """
        try:
            response = self.session.get(release_url, timeout=self.timeout)
            response.raise_for_status()
            content = response.text

            # Parse Release file for Architectures field
            arch_pattern = r'^Architectures:\s*(.+)$'
            match = re.search(arch_pattern, content, re.MULTILINE)
            
            if match:
                archs = match.group(1).strip().split()
                return archs
            
            return []
        except requests.RequestException:
            return []

    def get_components(self, release_url: str) -> List[str]:
        """
        Extract components from Release file.

        Args:
            release_url: URL of Release/InRelease file

        Returns:
            List of components (e.g., main, contrib, non-free)
        """
        try:
            response = self.session.get(release_url, timeout=self.timeout)
            response.raise_for_status()
            content = response.text

            # Parse Release file for Components field
            comp_pattern = r'^Components:\s*(.+)$'
            match = re.search(comp_pattern, content, re.MULTILINE)
            
            if match:
                components = match.group(1).strip().split()
                return components
            
            return []
        except requests.RequestException:
            return []
