"""apt-registry-explorer - A utility to explore APT repositories without needing apt-source setup or root access."""

__all__ = ["cli", "discovery", "packages", "sources", "tui"]

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"
