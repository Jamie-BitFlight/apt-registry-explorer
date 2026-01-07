# CLAUDE.md - AI Assistant Guide for apt-registry-explorer

This document provides comprehensive guidance for AI assistants working with this codebase.

## Repository Overview

**Purpose:** Python utility to validate and explore APT registry endpoints without requiring apt-source configuration or root access.

**Key Features:**
- Interactive repository discovery and navigation
- Terminal User Interface (TUI) for browsing packages with fzf-style search
- CLI tools for querying packages with JSON output (similar to apt-cache)
- APT sources configuration file generator (deb822 and one-line formats)

## Quick Reference

```bash
# Install dependencies
uv sync

# Run tests (must pass before commits)
uv run pytest

# Run linting and formatting
uv run ruff format packages/apt-registry-explorer/src tests/
uv run ruff check packages/apt-registry-explorer/src tests/

# Type checking
uv run mypy packages/apt-registry-explorer/src
uv run basedpyright packages/apt-registry-explorer/src

# Run the CLI
uv run apt-registry-explorer --help
```

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11 - 3.14 |
| Package Manager | uv (Astral) | latest |
| Build System | hatchling + hatch-vcs | - |
| CLI Framework | Typer | >=0.21.0 |
| TUI Framework | Textual | >=0.40.0 |
| HTTP Client | httpx | >=0.27.0 |
| Data Validation | Pydantic | >=2.0.0 |
| Type Checking | mypy + basedpyright | strict |
| Linting/Formatting | ruff | >=0.9.4 |
| Testing | pytest + pytest-asyncio | - |

## Project Structure

```
apt-registry-explorer/
├── packages/apt-registry-explorer/src/apt_registry_explorer/
│   ├── __init__.py           # Package exports and version
│   ├── cli.py                # Typer CLI commands with SOLID architecture
│   ├── discovery.py          # Repository navigation and Release file parsing
│   ├── packages.py           # Package metadata parsing (Pydantic models)
│   ├── sources.py            # APT sources file builder (Pydantic models)
│   ├── tui.py                # Textual TUI application
│   └── tui.tcss              # External CSS for TUI styling
├── tests/
│   ├── test_cli.py           # CLI command tests
│   ├── test_cli_solid_classes.py  # SOLID class unit tests
│   ├── test_discovery.py     # Discovery module tests
│   ├── test_packages.py      # Package parsing tests
│   ├── test_sources.py       # Sources builder tests
│   ├── test_tui_comprehensive.py  # TUI component tests
│   ├── test_integration.py   # Integration tests (real network)
│   └── fixtures/             # Test data files
├── .github/workflows/
│   ├── test.yml              # Main CI workflow
│   └── regenerate-screenshot.yml  # TUI screenshot generator
├── pyproject.toml            # Project configuration
└── README.md                 # User documentation
```

## Architecture

### SOLID Principles

The CLI module (`cli.py`) follows SOLID principles with dedicated classes:

| Class | Responsibility |
|-------|----------------|
| `SourceParser` | Parse source formats (URLs, deb lines) |
| `ArchitectureLister` | List and format architecture information |
| `PackageQuerier` | Query, filter, and output packages |
| `RepositoryExplorer` | Discover repository structure |

### Data Models (Pydantic)

All structured data uses Pydantic `BaseModel`:
- `PackageMetadata` - Package information from Packages file
- `SourceEntry` - APT source configuration entry
- `SourceOptions` - Source options (signed-by, arch, etc.)
- `ParsedDebLine` - Parsed deb line components

### Modern Python Features

This codebase uses Python 3.11+ features:
- Built-in generics: `list[X]`, `dict[K, V]` (not `typing.List`)
- Pipe unions: `X | None` (not `Optional[X]`)
- Match-case statements for control flow
- `StrEnum` for type-safe enumerations
- Walrus operator (`:=`) for assignment expressions
- `Annotated` types for Typer CLI parameters

## Development Workflow

### Before Starting Work

```bash
# Ensure dependencies are synced
uv sync

# Check current test status
uv run pytest -v
```

### Code Quality Checks (Required Before Commits)

```bash
# 1. Format code
uv run ruff format packages/apt-registry-explorer/src tests/

# 2. Run linter
uv run ruff check packages/apt-registry-explorer/src tests/

# 3. Type check with mypy
uv run mypy packages/apt-registry-explorer/src --show-error-codes --pretty

# 4. Type check with basedpyright
uv run basedpyright packages/apt-registry-explorer/src
```

### Testing

```bash
# Run all tests with coverage
uv run pytest

# Run unit tests only (faster, no network)
uv run pytest -m "not integration"

# Run integration tests only (requires network)
uv run pytest -m "integration"

# Run specific test file
uv run pytest tests/test_cli.py -v

# Run with more verbose output
uv run pytest -v --tb=short
```

### Running the Application

```bash
# Show help
uv run apt-registry-explorer --help

# Query packages
uv run apt-registry-explorer query --source "deb http://archive.ubuntu.com/ubuntu jammy main" --list-arch
uv run apt-registry-explorer query --source "deb http://archive.ubuntu.com/ubuntu jammy main" --arch amd64 --package bash

# Discover repository
uv run apt-registry-explorer discover https://example.com/debian
```

## Coding Conventions

### DO

- Use Pydantic `BaseModel` for all structured data types
- Add type hints to all functions with return annotations
- Use built-in generics (`list`, `dict`, `tuple`) not `typing` module
- Use pipe unions (`X | None`) not `Optional`
- Let Typer handle exceptions automatically
- Keep functions focused and small (< 15 lines when possible)
- Follow existing SOLID class patterns in `cli.py`
- Access Pydantic model fields as attributes (not dict keys)

### DON'T

- Use `TypedDict` or `@dataclass` (use Pydantic `BaseModel`)
- Catch and re-raise exceptions in Typer commands
- Import from `typing` for built-in generics
- Add complexity warnings suppressions (`# noqa`) - refactor instead
- Create mocks for Pydantic models in tests without proper instantiation

### Error Handling in Typer

```python
# CORRECT - Let Typer handle it
def my_command():
    if not valid:
        typer.echo("Error: message", err=True)
        raise typer.Exit(1)
    # proceed...

# WRONG - Don't catch and re-raise
def my_command():
    try:
        do_something()
    except SomeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e  # Anti-pattern!
```

### Pydantic Model Access

```python
# CORRECT - Access as attributes
parsed = builder.parse_deb_line(source)
url = parsed.url
suite = parsed.suite

# WRONG - Don't treat as dict
url = parsed["url"]  # TypeError!
```

## CI/CD Pipeline

### GitHub Actions Structure

The `test.yml` workflow runs on push/PR to `main` and `develop`:

1. **Quality Job** (Python 3.12)
   - `ruff format --check` - Verify formatting
   - `ruff check` - Lint with GitHub annotations
   - `mypy` - Type checking
   - `basedpyright` - Additional type checking

2. **Tests Job** (Python 3.11-3.14 matrix)
   - Runs after quality checks pass
   - All tests (unit + integration) with coverage
   - CLI entry point validation

### Action Versions

Always use latest major versions:
- `actions/checkout@v6`
- `actions/setup-python@v6`
- `astral-sh/setup-uv@v5`

## Common Tasks

### Adding a New CLI Command

1. Create a SOLID class for command logic in `cli.py`
2. Add `@app.command()` decorated function that delegates to the class
3. Use `Annotated` types for parameters
4. Let Typer handle exceptions
5. Write unit tests mocking external dependencies
6. Update README with usage examples

### Adding a New Pydantic Model

```python
from pydantic import BaseModel

class MyModel(BaseModel):
    """Docstring explaining the model."""

    field_name: str
    optional_field: str | None = None
    list_field: list[str] | None = None

    model_config = {"extra": "allow"}  # If needed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
```

### Writing Tests

```python
import pytest
from unittest.mock import MagicMock, patch

# Unit test with mocking
def test_something() -> None:
    """Test description."""
    with patch("apt_registry_explorer.module.external_call") as mock:
        mock.return_value = expected_value
        result = function_under_test()
        assert result == expected

# Integration test (real network)
@pytest.mark.integration
def test_real_api() -> None:
    """Test against real Ubuntu repository."""
    # Makes real HTTP requests
    result = fetch_real_data()
    assert result is not None
```

### Updating Dependencies

1. Update versions in `pyproject.toml`
2. Run `uv lock` to update lockfile
3. Run full test suite: `uv run pytest`
4. Update workflow action versions if needed

## Test Fixtures

Test fixtures are located in `tests/fixtures/`:
- `packages_file.txt` - Sample Packages file content
- `release_file.txt` - Sample Release file content

## Coverage Requirements

- Current baseline: 70% (`fail_under` in pyproject.toml)
- Target: 80%+ incrementally
- Each SOLID class method should have corresponding tests

## Integration Test Repository

Integration tests use Ubuntu's Jammy (22.04) repository:
- URL: `http://archive.ubuntu.com/ubuntu/`
- Suite: `jammy`
- Components: `main`, `universe`
- Architectures: `amd64`, `arm64`

## Troubleshooting

### Common Issues

**Import errors in tests:**
```bash
# Ensure pythonpath is set correctly
uv run pytest --collect-only  # Check test discovery
```

**Type checking errors:**
```bash
# Check specific file
uv run mypy packages/apt-registry-explorer/src/apt_registry_explorer/cli.py
```

**Formatting issues:**
```bash
# Auto-fix with ruff
uv run ruff format packages/apt-registry-explorer/src tests/
uv run ruff check --fix packages/apt-registry-explorer/src tests/
```

## File Locations Quick Reference

| What | Where |
|------|-------|
| Main CLI entry | `packages/.../cli.py` |
| Pydantic models | `packages/.../packages.py`, `packages/.../sources.py` |
| TUI application | `packages/.../tui.py` |
| TUI styles | `packages/.../tui.tcss` |
| Test configuration | `pyproject.toml` `[tool.pytest.ini_options]` |
| Ruff configuration | `pyproject.toml` `[tool.ruff]` |
| Type checker config | `pyproject.toml` `[tool.mypy]`, `[tool.basedpyright]` |
| CI workflow | `.github/workflows/test.yml` |
