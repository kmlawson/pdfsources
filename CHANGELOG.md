# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-07-19

### Added

- Initial project setup with citation extraction and bibliography generation
- Support for Chicago, APA, and Harvard citation styles
- Multiple output formats: divided, combined, sources, and sources-divided
- Security fixes: path traversal protection, markdown injection prevention
- Automation support: --force and --no-interaction flags
- Secure subprocess handling with path validation

### Security

- Fixed path traversal vulnerability in version detection
- Added markdown escaping to prevent injection attacks
- Implemented secure file path validation for subprocess calls
