# OARepo Runtime - Copilot Coding Agent Instructions

## Repository Overview

**OARepo Runtime** is a Python extension library that provides runtime support for the OARepo system (a specialized Invenio-based repository platform). It extends Invenio Records Resources with additional features for research data management, custom fields, facets, relations, validation, and internationalization.

**Key Facts:**
- Type: Python library/extension for Invenio
- Size: ~50 Python files, ~20 test files, small-to-medium codebase 
- Languages: Python (primary), YAML/JSON configuration
- Framework: Invenio (built on Flask), extends Invenio Records Resources
- Target: Python 3.13 **ONLY** (strict requirement - will fail on other versions)
- OARepo Version: 13 (specified in dependencies)
- License: MIT

## Critical Build & Environment Requirements

### Python Version Requirement (CRITICAL)
- **MUST USE Python 3.13.x** - This is a hard requirement in pyproject.toml (`requires-python = ">=3.13,<3.14"`)
- Building with Python 3.12 or older **WILL FAIL** 
- The mock-module test dependency also requires Python 3.13
- Use `PYTHON_VERSION=3.13 PYTHON=python3.13` environment variables

### Build System & Dependencies
- Build system: `hatchling` (modern Python packaging)
- Primary dependencies: `oarepo[rdm,tests]>=13,<14`, `langcodes>=3.5.0`
- Package manager: `uv` (ultra-fast Python package installer) - **REQUIRED**
- Test dependencies require `pytest-invenio` and other Invenio test fixtures

### Build Commands - **ALWAYS USE THESE IN ORDER**

**Environment Setup:**
```bash
# Set up virtual environment with correct Python version
PYTHON_VERSION=3.13 PYTHON=python3.13 ./run.sh venv
```

**Build & Test:**
```bash
# Install the package in development mode
./run.sh venv

# Start external services (required for tests)
docker compose -f docker-compose.test.yml up -d

# Install test module dependencies  
./test-setup.sh

# Run tests
./run.sh test

# Stop services
docker compose -f docker-compose.test.yml down
```

**Linting & Formatting:**
```bash
./run.sh lint      # Run linters (includes ruff, mypy)
./run.sh format    # Format code with ruff
```

**Other Commands:**
```bash
./run.sh clean                    # Clean environment
./run.sh oarepo-versions         # Show supported versions  
./run.sh translations           # Handle i18n
./run.sh license-headers        # Add license headers
```

### External Service Dependencies

**Required for Testing (via Docker Compose):**
- OpenSearch 2.13.0 (port 9200) - for search functionality
- Redis 7 (port 6379) - for caching
- PostgreSQL (for full integration tests)

**Start services before testing:**
```bash
docker compose -f docker-compose.test.yml up -d
```

## Project Architecture & Layout

### Main Package Structure (`oarepo_runtime/`)
- `api.py` - Main API classes and Model definitions
- `ext.py` - Flask extension (OARepoRuntime class) 
- `cli/` - Command line interface extensions
  - `__init__.py` - CLI command registration (oarepo, index, assets, check, validate, fixtures, etc.)
  - `search.py` - Search index extensions
- `records/` - Record-related functionality
  - `systemfields/` - Custom system fields (mapping, publication_status)
  - `drafts.py`, `mapping.py`, `pid_providers.py` - Core record functionality
- `services/` - Business logic layer
  - `config/` - Service configuration (permissions, components)
  - `records/` - Record service extensions
  - `facets/` - Faceted search functionality
- `resources/` - REST API resources
- `ext_config.py` - Extension configuration defaults

### Configuration Files
- `pyproject.toml` - **PRIMARY** build configuration (hatchling, dependencies, entry points)
- `babel.cfg` - Internationalization extraction config
- `babel.ini` - Translation compilation config  
- `oarepo.yaml` - OARepo-specific i18n configuration
- `MANIFEST.in` - Package manifest (includes YAML/JSON files)
- `docker-compose.test.yml` - Test services configuration

### Test Structure (`tests/`)
- `conftest.py` - Main pytest configuration and fixtures
- `mock-module/` - Test package with complete Invenio entry points
- `service_components/` - Component ordering and dependency tests
- Various test files covering API, CLI, services, records, etc.

### GitHub Workflows & CI
- `.github/workflows/test.yaml` - Delegates to main OARepo repository workflow
- `.github/workflows/release.yaml` - Delegates to main OARepo repository release workflow  
- Uses **shared workflow system** from main `oarepo/oarepo` repository

## Command Line Interface

This package provides `invenio oarepo` commands (registered via Flask CLI):

**Key Commands:**
- `invenio oarepo check [output-file]` - Infrastructure health check (DB, OpenSearch, files, cache)
- `invenio oarepo version` - Show installed package versions
- `invenio oarepo cf init` - Initialize custom fields
- `invenio oarepo index init` - Initialize search indices with dynamic mappings
- `invenio oarepo fixtures load` - Load test/sample data
- `invenio oarepo assets collect` - Collect static assets

## Development Workflow & Validation

### Pre-commit Validations
Run these checks before any code changes:
```bash
./run.sh lint         # Linting (ruff, mypy, etc.)
./run.sh format       # Auto-format code
./run.sh test         # Full test suite
```

### Common Pitfalls & Workarounds
1. **Python Version Issues**: Always check Python version first - must be 3.13.x
2. **Network Connectivity**: The build system needs access to `gitlab.cesnet.cz` package index
3. **Service Dependencies**: Tests will fail without OpenSearch/Redis running
4. **Mock Module**: Always run `./test-setup.sh` before testing to install test dependencies
5. **UV Package Manager**: Install `uv` if getting "command not found" errors

### Making Changes
1. Always test locally with `./run.sh test` before submitting
2. The test suite includes component ordering, service integration, and CLI functionality
3. Mock module in `tests/mock-module/` provides complete test environment
4. Known TODOs exist in `services/results.py` and `services/facets/params.py` - these are documented design decisions

## Entry Points & Extensions

The package registers multiple Invenio entry points:
- `invenio_base.api_apps` / `invenio_base.apps` - Main extension
- `flask.commands` - CLI commands
- Various service, component, and configuration extensions

## Trust These Instructions

This repository uses a sophisticated shared tooling system via the main OARepo repository. The `./run.sh` script downloads and uses shared build/test infrastructure, so always prefer the documented commands over manual pip/pytest usage. Only explore alternative approaches if the documented commands fail or if instructions are incomplete.