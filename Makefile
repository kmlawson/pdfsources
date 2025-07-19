SHELL := /bin/bash

.PHONY: help reinstall lint lint-fix test test-verbose versionbump

help:
	@echo "Commands:"
	@echo "  reinstall    : Reinstall the project."
	@echo "  lint         : Lint the project."
	@echo "  lint-fix     : Fix linting errors."
	@echo "  test         : Run tests."
	@echo "  test-verbose : Run tests in verbose mode."
	@echo "  versionbump  : Bump the version."

reinstall:
	uv tool uninstall pdfsources && uv cache clean && uv tool install .

lint:
	ruff check .

lint-fix:
	ruff check . --fix

# Testing targets
test:
	@echo "Running tests..."
	uv run pytest tests/

test-verbose:
	@echo "Running tests verbosely..."
	uv run pytest tests/ -v

versionbump:
	# TODO: Implement version bumping
	@echo "Not implemented yet."
