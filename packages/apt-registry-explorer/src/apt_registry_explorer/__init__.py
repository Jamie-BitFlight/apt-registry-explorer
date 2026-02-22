"""apt-registry-explorer - A utility to explore APT repositories without needing apt-source setup or root access."""

from . import cli, discovery, packages, sources, tui
from ._meta import __version__

__all__ = ["__version__", "cli", "discovery", "packages", "sources", "tui"]
