# apt-registry-explorer

A Python utility to validate and explore APT registry endpoints to check for available distributions, channels, and packages without needing the apt-source set up, or root access.

**Requirements:** Python 3.11 or higher

## Features

- **Interactive Discovery**: Navigate APT repository URLs interactively to discover distributions, architectures, and components
- **TUI Package Browser**: Terminal user interface with fzf-style package browsing and split-pane information display
- **CLI Tools**: Command-line interface built with Typer for querying packages with JSON output similar to apt-cache
- **APT Sources Builder**: Generate apt.sources configuration files with GPG/arch/signed-by options
- **Modern Python**: Uses Python 3.11+ features including built-in generics, match-case statements, and pipe unions

## Installation

```bash
pip install apt-registry-explorer
```

**Note:** Requires Python 3.11 or higher.

### Development Installation with uv (Recommended)

This project uses [uv](https://docs.astral.sh/uv/) from Astral for fast, reliable dependency management.

```bash
# Install uv if you haven't already
pip install uv

# Clone the repository
git clone https://github.com/Jamie-BitFlight/apt-registry-explorer.git
cd apt-registry-explorer

# Install with uv (recommended)
uv pip install -e ".[dev]"

# Or sync all dependencies including dev
uv sync --all-extras
```

### Alternative Installation with pip

```bash
# Clone the repository
git clone https://github.com/Jamie-BitFlight/apt-registry-explorer.git
cd apt-registry-explorer

# Install with pip
pip install -e ".[dev]"
```

## Dependencies

This project uses modern Python frameworks:
- **Typer** (>=0.21.0) - For the CLI interface with rich formatting
- **Textual** (from textualize.io) - For the TUI package browser
- **Rich** (from textualize.io) - For terminal formatting and output
- **uv** (from Astral) - For dependency management (dev workflow)

## Usage

### Interactive Discovery

Explore a repository structure and generate sources configuration:

```bash
apt-registry-explorer discover https://example.com/debian
```

This will:
- List available directories
- Find distribution suites
- Display architectures and components
- Generate apt.sources configuration

### CLI Query

Query packages from a repository:

```bash
# List available architectures
apt-registry-explorer query --source https://example.com/debian --list-arch

# Query packages for a specific architecture
apt-registry-explorer query --source https://example.com/debian --arch amd64 --package python3

# Search with regex pattern
apt-registry-explorer query --source https://example.com/debian --arch amd64 --regex "^python3-.*"

# Filter by version
apt-registry-explorer query --source https://example.com/debian --arch amd64 --package python3 --version ">=3.9"

# Use a deb line as source
apt-registry-explorer query --source "deb https://example.com/debian stable main" --arch amd64 --package nginx
```

### TUI Package Browser

Launch the interactive TUI (requires loading packages first):

```python
from apt_registry_explorer.packages import PackageIndex
from apt_registry_explorer.tui import launch_tui

# Load packages
index = PackageIndex()
index.load_from_url("https://example.com/debian", "amd64", "main")

# Launch TUI
launch_tui(index.get_all_packages())
```

## Command-Line Options

### `discover` Command

```
Usage: apt-registry-explorer discover [OPTIONS] URL

  Interactively discover repository structure and generate sources configuration.

Options:
  --format [deb822|oneline]  Output format (default: deb822)
  --help                     Show this message and exit.
```

### `query` Command

```
Usage: apt-registry-explorer query [OPTIONS]

  Query APT repository for package information.

Options:
  --source TEXT               Repository URL or deb line [required]
  --list-arch                 List available architectures
  --arch TEXT                 Architecture to query (e.g., amd64)
  --package TEXT              Package name to search
  --version TEXT              Version specification (e.g., >=1.0)
  --regex TEXT                Regex pattern to match package names
  --component TEXT            Component to query (default: main)
  --output [json|text]        Output format (default: json)
  --help                      Show this message and exit.
```

## Output Format

The tool outputs package metadata in JSON format similar to apt-cache:

```json
[
  {
    "package": "python3",
    "version": "3.11.2-1",
    "architecture": "amd64",
    "maintainer": "Example Maintainer <maintainer@example.com>",
    "installed_size": "1024",
    "depends": "python3-minimal (= 3.11.2-1)",
    "section": "python",
    "priority": "important",
    "description": "Interactive high-level object-oriented language",
    "filename": "pool/main/p/python3/python3_3.11.2-1_amd64.deb",
    "size": "2048",
    "sha256": "abc123..."
  }
]
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black packages/apt-registry-explorer/src tests
```

### Linting

```bash
ruff check packages/apt-registry-explorer/src tests
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
