# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2025-07-19

### Added
- Comprehensive data cleaning and normalization layer for PDF extraction artifacts
- Enhanced author name normalization with proper handling of particles (van, von, de, etc.)
- Advanced citation filtering to remove junk entries and improve bibliography quality
- Automatic deduplication system with signature-based matching across multiple files
- Enhanced citation type inference with heuristic-based categorization
- Extensive test coverage with 100 tests including edge cases and security validation

### Improved
- Renamed "Generic" category to "Other" following academic conventions
- Enhanced has_valid_content() validation with comprehensive junk pattern detection
- Modular architecture with clean separation of concerns across multiple modules
- Better categorization of citation types (thesis, reports, etc.)
- Container-title field mapping from anystyle's hyphenated format

### Fixed
- Double backslash removal from PDF extraction artifacts
- Escaped character handling from anystyle processing
- HTML entity cleanup in citation text
- ALL CAPS author name normalization to proper Title Case
- APA formatter journal name inclusion in article citations
- Test validation patterns for improved reliability

### Security
- Enhanced markdown escaping with HTML tag prevention
- Improved input validation and error handling
- Comprehensive filtering of malicious or low-quality content

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
