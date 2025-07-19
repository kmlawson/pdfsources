# Development Guide

This document provides an overview of the pdfsources project structure, implemented features, and development patterns for contributors and maintainers.

## Project Overview

pdfsources is a tool for extracting and processing citations from PDF files. It processes JSON output from citation extraction tools (primarily anystyle) and generates formatted bibliographies in multiple citation styles.

### Core Dependency: anystyle

The project relies on **anystyle** as its primary citation extraction engine:
- **Language**: Ruby-based command-line tool
- **Installation**: `gem install anystyle-cli`
- **Purpose**: Extracts citation data from PDF files and outputs structured JSON
- **Integration**: pdfsources calls anystyle via subprocess to process PDFs

**Critical**: Without anystyle installed, the tool can only process existing JSON files and cannot extract citations from PDFs directly.

## Project Structure

The project follows the standard Python packaging layout recommended for PyPI distribution:

```
pdfsources/
├── LICENSE                  # MIT license file
├── README.md               # User documentation and installation instructions
├── pyproject.toml          # Modern Python packaging configuration
├── Makefile                # Development automation commands
├── CHANGELOG.md            # Version history and release notes
├── TODO.md                 # Task tracking and roadmap
├── DEVELOPMENT.md          # This file - developer documentation
├── CONTRIBUTING.md         # Contribution guidelines
├── MANIFEST.in             # Additional files to include in distributions
├── setup.py                # Legacy setup file for compatibility
│
├── src/pdfsources/         # Main application code (src layout)
│   ├── __init__.py         # Package initialization (minimal)
│   ├── __main__.py         # Main CLI application and citation formatting
│   └── combine_anystyle_output.py  # Utility for combining anystyle JSON outputs
│
├── tests/                  # Unit tests
│   └── test_process_citations.py   # Tests for citation processing functionality
│
├── info/                   # Reference documentation and data files
│   ├── anystyle-report-*.json     # Sample citation extraction results
│   └── raw_anystyle_output/       # Raw extraction output from anystyle
│
├── pdfs/                   # PDF source files for processing (samples)
│
└── reference/              # Notes on similar projects and research
```

**Key Structural Decisions:**
- **src/ layout**: Recommended best practice for PyPI packages
- **setuptools backend**: Reliable build system with excellent src/ layout support  
- **MIT License**: Permissive open-source license in dedicated LICENSE file
- **pyproject.toml**: Modern packaging standard with complete metadata

## Core Scripts and Modules

### `src/pdfsources/__main__.py`
The main application entry point containing:

- **Configuration Management**: Uses platformdirs for cross-platform config storage
- **Citation Formatting Functions**:
  - `format_chicago()`: Chicago Manual of Style formatting
  - `format_apa()`: APA style formatting  
  - `format_harvard()`: Harvard referencing style
- **Utility Functions**:
  - `get_author_string()`: Formats author/editor names
  - `get_first_item()`: Safely extracts list items from references
  - `infer_type()`: Determines reference type (book, article, etc.)
- **Main Processing**: `process_files()` handles different output formats
- **CLI Interface**: Full argument parsing with multiple output options

### `src/pdfsources/combine_anystyle_output.py`
Utility script for merging multiple anystyle JSON outputs into a single file:
- Reads from `info/raw_anystyle_output/` directory
- Combines all JSON files into `info/anystyle-report-full.json`
- Handles JSON decode errors gracefully

## Currently Implemented Features

### Citation Style Support
- **Chicago Manual of Style**: Default style with full formatting
- **APA Style**: Academic Psychology Association format
- **Harvard Referencing**: Author-date citation system

### Output Formats
- **Divided Output**: Groups citations by type (books, articles, etc.)
- **Combined Output**: Single alphabetically sorted bibliography
- **Sources Output**: Groups citations by original PDF source file

### Reference Type Detection
Automatic inference of reference types based on available fields:
- Books (has publisher/location fields)
- Journal articles (has container-title)
- Generic fallback for unclear types

### Configuration Management
- TOML-based configuration in user config directory
- Default settings for output file names and citation style
- Automatic config file creation with sensible defaults

### Error Handling and Logging
- Comprehensive logging with debug mode support
- Graceful handling of malformed JSON files
- Filtering of incomplete or invalid references (< 20 chars, "ibid" entries)

## Development Patterns

### Code Style and Quality
- **PEP 8 Compliance**: All code follows Python style guidelines
- **Ruff Integration**: Use `make lint` and `make lint-fix` for code quality
- **Modular Functions**: Small, focused functions with single responsibilities
- **Type Safety**: Uses pydantic for data validation where appropriate

### Testing Approach
- **Unit Tests**: Comprehensive test coverage in `tests/test_process_citations.py`
- **Test-Driven Development**: Write tests before implementing new features
- **pytest Framework**: Use `make test` to run the test suite

### Version Control and Release
- **Semantic Versioning**: 0.0.x increments for new features
- **Changelog Maintenance**: Update CHANGELOG.md with each release
- **Git Workflow**: Feature branches with clean commit messages

### Build and Development Tools
- **Makefile Automation**:
  - `make reinstall`: Clean reinstall of the package
  - `make lint`: Code quality checks
  - `make lint-fix`: Automatic code formatting fixes
  - `make test`: Run test suite
  - `make test-verbose`: Verbose test output
  - `make versionbump`: Increment version numbers
  - `make help`: Show available targets

### Dependency Management
- **uv**: Modern Python package manager for dependencies
- **pyproject.toml**: Modern Python packaging configuration
- **setup.py**: Maintained for backward compatibility

## Key Development Guidelines

### Adding New Features
1. Create unit tests first (TDD approach)
2. Implement feature in modular, focused functions
3. Update documentation (README.md, help text)
4. Run full test suite and linting
5. Update CHANGELOG.md

### Citation Style Implementation
When adding new citation styles:
1. Create a `format_[style]()` function following existing patterns
2. Add style to the `formatters` dictionary in `process_files()`
3. Add style choice to CLI argument parser
4. Write comprehensive tests for the new style

### Code Organization Principles
- Keep functions small and focused (single responsibility)
- Separate formatting logic from file processing logic
- Use helper functions for common operations (e.g., `get_first_item`)
- Maintain consistent error handling patterns
- Follow existing naming conventions

### Security Considerations
- Never commit secrets or API keys
- Use gitleaks for secret scanning
- Validate all external inputs (JSON files, user arguments)
- Handle file operations safely with proper error checking

## Deployment Process

### Local Development
1. **Install poppler-utils first**: 
   - macOS: `brew install poppler`
   - Ubuntu/Debian: `sudo apt-get install poppler-utils`
   - CentOS/RHEL: `sudo yum install poppler-utils`
   - Fedora: `sudo dnf install poppler-utils`
2. **Install anystyle**: `gem install anystyle-cli`
3. **Verify all dependencies work**: 
   - `anystyle --version`
   - `pdftotext -v`
   - `pdfinfo -v`
4. `make reinstall` - Install package locally
5. `make lint` - Check code quality
6. `make test` - Run test suite
7. Test functionality manually with sample data

**Troubleshooting**: If PDF processing fails, ensure:
- Ruby is installed (`ruby --version`)
- poppler-utils is installed (`pdftotext -v` and `pdfinfo -v` should work)
- anystyle gem is installed (`gem list | grep anystyle`)
- anystyle command is accessible (`which anystyle`)

### PyPI Release (when ready)
1. Increment version with `make versionbump`
2. Update CHANGELOG.md with new features/fixes
3. Run full test suite and ensure all pass
4. Clean build: `rm -rf dist/ && uv build`
5. Upload with twine (not uv publish due to credential issues)

## Integration Points

### External Tools
- **anystyle**: **PRIMARY DEPENDENCY** - Ruby-based citation extraction tool (gem install anystyle-cli)
- **GROBID**: Alternative extraction tool for comparison (optional)

### Input/Output Formats
- **Input**: JSON files from citation extraction tools
- **Output**: Markdown formatted bibliographies
- **Configuration**: TOML files for user preferences

This development guide should be updated as new features are added and development patterns evolve.