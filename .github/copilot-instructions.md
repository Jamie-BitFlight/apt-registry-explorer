# Copilot Instructions for apt-registry-explorer

## Repository Overview

**Purpose:** Python utility to validate and explore APT registry endpoints without requiring apt-source configuration or root access.

**Project Type:** Python command-line tool with TUI (Terminal User Interface)  
**Size:** ~450 KB, 13 Python modules  
**Target Runtime:** Python 3.11-3.14  
**Package Manager:** uv (from Astral)  
**Build System:** hatchling with hatch-vcs for version management

**Key Frameworks:**

- **Typer >=0.21.0** - CLI framework with Annotated syntax (includes Rich for formatting)
- **Textual** - Terminal UI framework from textualize.io
- **httpx >=0.27.0** - Async HTTP client
- **Pydantic >=2.0.0** - Data validation and parsing

**Modern Python Features Used:**

- Built-in generics (`list[X]`, `dict[K, V]`) instead of typing module aliases
- Pipe unions (`X | None`) instead of Optional
- Match-case statements for control flow
- StrEnum for type-safe enumerations
- Walrus operator (`:=`) for assignment expressions

## Project Structure

```
packages/apt-registry-explorer/src/apt_registry_explorer/  # Source code
├── __init__.py           # Package metadata and version
├── cli.py               # Typer CLI commands with SOLID architecture
├── discovery.py         # Repository navigation and Release file parsing
├── packages.py          # Package metadata parsing (uses Pydantic models)
├── sources.py           # APT sources file builder (uses Pydantic models)
├── tui.py              # Textual TUI application
└── tui.tcss            # External CSS for TUI styling

tests/                   # Test suite (20 unit tests + 4 integration tests)
├── test_*.py           # Unit tests for each module
└── test_integration.py  # Integration tests against real Ubuntu repository

.github/workflows/       # CI/CD workflows
├── test.yml            # Main test workflow (quality, unit, integration)
└── regenerate-screenshot.yml  # Manual workflow for TUI screenshots
```

## Architecture & Code Quality

**SOLID Principles Applied:**

- `SourceParser` - Parses different source formats (URLs, deb lines)
- `ArchitectureLister` - Lists and formats architecture information
- `PackageQuerier` - Queries, filters, and outputs packages
- `RepositoryExplorer` - Discovers repository structure

**Type Safety:**

- All functions have comprehensive type hints with return annotations
- Use Pydantic BaseModel for structured data (not TypedDict or dataclass)
- Strict mypy and basedpyright checking enabled

**Error Handling:**

- Let Typer handle exceptions automatically - DO NOT catch and re-raise
- Only catch exceptions if you're handling them differently
- Never print error + raise another exception (anti-pattern in Typer)

## Build & Development Workflow

### Bootstrap

```bash
# Install uv (one-time setup)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and sync dependencies
git clone <repo-url>
cd apt-registry-explorer
uv sync
```

### Code Quality (ALWAYS run before committing)

```bash
# Format code
uv run ruff format packages/apt-registry-explorer/src tests/

# Lint code
uv run ruff check packages/apt-registry-explorer/src tests/

# Type check with mypy
uv run mypy packages/apt-registry-explorer/src --show-error-codes --pretty

# Type check with basedpyright
uv run basedpyright packages/apt-registry-explorer/src
```

### Testing (ALWAYS run before pushing commits)

```bash
# Run unit tests only (fast, no network)
uv run pytest tests/ -v -m "not integration"

# Run integration tests (takes ~5-10 seconds, requires network)
uv run pytest tests/ -v -m "integration"

# Run all tests with coverage
uv run pytest tests/ -v --cov=apt_registry_explorer --cov-report=term
```

### Running the Application

```bash
# Run CLI commands
uv run apt-registry-explorer --help
uv run apt-registry-explorer query --source "deb http://archive.ubuntu.com/ubuntu jammy main" --list-arch
uv run apt-registry-explorer discover https://example.com/debian
```

## CI/CD Workflow

**GitHub Actions Structure:**

1. **Quality Job** - Runs once on Python 3.12
   - ruff format check (fails if not formatted)
   - ruff check with GitHub annotations
   - mypy type checking
   - basedpyright type checking

2. **Unit Tests Job** - Runs once on Python 3.12
   - Tests excluding integration marker
   - CLI entry point validation (help system only)

3. **Integration Tests Job** - Matrix across Python 3.11-3.14
   - Tests marked with @pytest.mark.integration
   - Tests against real Ubuntu Jammy repository
   - Validates network operations and real data parsing

**Action Versions:** Always use latest major versions:

- actions/checkout@v6
- actions/setup-python@v6
- astral-sh/setup-uv@v5

## Important Guidelines

**DO:**

- Use Pydantic BaseModel for all structured data types
- Follow SOLID principles - single responsibility per class
- Let Typer handle exceptions automatically
- Run all quality checks before committing
- Add type hints to all functions
- Keep functions small (<15 lines when possible)
- Use built-in generics (list, dict, tuple) not typing module
- Use pipe unions (X | None) not Optional

**DON'T:**

- Use TypedDict or dataclass (use Pydantic BaseModel)
- Catch and re-raise exceptions in Typer commands
- Suppress complexity warnings with noqa (refactor instead)
- Add "slow" marker to tests (integration marker is sufficient)
- Use outdated action versions in workflows
- Import from typing for built-in generics

## Testing Philosophy

- Unit tests mock external dependencies (HTTP, file I/O)
- Integration tests (@pytest.mark.integration) test against real Ubuntu repos
- Coverage baseline: 47% (incrementally improving)
- Each SOLID class method should have corresponding unit tests
- Test edge cases and error conditions

## Common Tasks

**Adding a new CLI command:**

1. Create a SOLID class for the command logic in cli.py
2. Add @app.command() decorated function that delegates to the class
3. Let Typer handle exceptions - don't wrap in try/catch
4. Add comprehensive type hints
5. Write unit tests mocking dependencies
6. Update README with command usage

**Updating dependencies:**

1. Check latest versions on respective release pages
2. Update pyproject.toml dependencies section
3. Run `uv lock` to update lockfile
4. Run full test suite to verify compatibility
5. Update workflows if action versions changed

**Improving test coverage:**

1. Identify untested methods in SOLID classes
2. Write focused unit tests with mocked dependencies
3. Aim for 80%+ coverage incrementally
4. Update pyproject.toml [tool.coverage.report] fail_under as coverage improves
