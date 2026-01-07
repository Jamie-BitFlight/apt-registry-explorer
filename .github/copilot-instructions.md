# Copilot Instructions for apt-registry-explorer

## CRITICAL: First Steps Before Any Work

**MANDATORY**: Run these commands before making any changes:

```bash
# 1. Install dependencies
uv sync

# 2. Install prek git hooks (REQUIRED - do this first!)
uv run prek install
```

## BANNED: Never Use --no-verify

**`git commit --no-verify` is STRICTLY FORBIDDEN.**

- There is NO scenario where `--no-verify` should be used
- All commits MUST pass prek hooks (ruff, mypy, basedpyright, prettier, pytest)
- If hooks fail, FIX THE CODE - do not bypass the hooks
- This applies to all commits, including "quick fixes" or "WIP" commits

If you encounter hook failures:

1. Run `uv run poe fix` to auto-fix formatting/linting issues
2. Run `uv run poe typecheck` to see type errors
3. Run `uv run poe test-fast` to debug test failures
4. Fix the issues, then commit normally

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
- **poethepoet (poe)** - Task runner for simplified commands
- **prek** - Rust-based git hooks (pre-commit replacement)

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

.pre-commit-config.yaml  # prek/pre-commit hooks configuration
pyproject.toml           # Project config + poe tasks
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

### Bootstrap (First Time Setup)

```bash
# Install uv (one-time setup)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and sync dependencies
git clone <repo-url>
cd apt-registry-explorer
uv sync

# Install prek git hooks (REQUIRED!)
uv run prek install

# Verify hooks are working
uv run prek run --all-files
```

### Using Poe Commands (Recommended)

All common tasks are available via `uv run poe <command>`:

```bash
# Formatting
uv run poe format        # Format code with ruff
uv run poe format-check  # Check formatting without changes

# Linting
uv run poe lint          # Run ruff linter
uv run poe lint-fix      # Run linter with auto-fix

# Type Checking
uv run poe mypy          # Run mypy
uv run poe pyright       # Run basedpyright
uv run poe typecheck     # Run both type checkers

# Testing
uv run poe test          # All tests with coverage
uv run poe test-unit     # Unit tests only (no network)
uv run poe test-integration  # Integration tests only
uv run poe test-fast     # Quick tests (no coverage, stop on failure)

# Combined Commands
uv run poe check         # format-check + lint + typecheck
uv run poe fix           # format + lint-fix
uv run poe all           # fix + typecheck + test

# Git Hooks
uv run poe prek-install  # Install git hooks
uv run poe prek-run      # Run all hooks on all files
uv run poe prek-update   # Update hook versions
```

### Running the Application

```bash
# Run CLI commands
uv run apt-registry-explorer --help
uv run apt-registry-explorer query --source "deb http://archive.ubuntu.com/ubuntu jammy main" --list-arch
uv run apt-registry-explorer discover https://example.com/debian
```

## prek Git Hooks

The `.pre-commit-config.yaml` configures these hooks that run on every commit:

| Hook                   | Purpose                       |
| ---------------------- | ----------------------------- |
| `ruff-format`          | Code formatting               |
| `ruff`                 | Linting with auto-fix         |
| `mypy`                 | Type checking                 |
| `basedpyright`         | Enhanced type checking        |
| `prettier`             | Format YAML/JSON/Markdown     |
| `pytest`               | Run unit tests                |
| `trailing-whitespace`  | Remove trailing whitespace    |
| `end-of-file-fixer`    | Ensure files end with newline |
| `check-yaml/json/toml` | Validate config files         |

## CI/CD Workflow

**GitHub Actions Structure:**

1. **Quality Job** - Runs once on Python 3.12
   - ruff format check (fails if not formatted)
   - ruff check with GitHub annotations
   - mypy type checking
   - basedpyright type checking

2. **Tests Job** - Matrix across Python 3.11-3.14
   - All tests (unit + integration) with coverage
   - CLI entry point validation

**Action Versions:** Always use latest major versions:

- actions/checkout@v6
- actions/setup-python@v6
- astral-sh/setup-uv@v5

## Important Guidelines

**DO:**

- Run `uv run prek install` before any work
- Use `uv run poe <command>` for all tasks
- Use Pydantic BaseModel for all structured data types
- Follow SOLID principles - single responsibility per class
- Let Typer handle exceptions automatically
- Add type hints to all functions
- Keep functions small (<15 lines when possible)
- Use built-in generics (list, dict, tuple) not typing module
- Use pipe unions (X | None) not Optional

**DON'T:**

- Use `git commit --no-verify` (NEVER!)
- Use TypedDict or dataclass (use Pydantic BaseModel)
- Catch and re-raise exceptions in Typer commands
- Suppress complexity warnings with noqa (refactor instead)
- Add "slow" marker to tests (integration marker is sufficient)
- Use outdated action versions in workflows
- Import from typing for built-in generics

## Testing Philosophy

- Unit tests mock external dependencies (HTTP, file I/O)
- Integration tests (@pytest.mark.integration) test against real Ubuntu repos
- Coverage baseline: 70% (`fail_under` in pyproject.toml)
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
4. Run `uv run poe all` to verify compatibility
5. Update workflows if action versions changed

**Improving test coverage:**

1. Identify untested methods in SOLID classes
2. Write focused unit tests with mocked dependencies
3. Aim for 80%+ coverage incrementally
4. Update pyproject.toml [tool.coverage.report] fail_under as coverage improves
