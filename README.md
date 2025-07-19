# pdfsources

A tool for extracting and processing citations from PDF files.

## Installation

### Prerequisites

**Required Dependencies:**

1. **Ruby** - Required for anystyle
2. **poppler-utils** - Provides `pdftotext` and `pdfinfo` tools needed by anystyle
3. **anystyle** - Ruby-based citation extraction tool

```bash
# Install poppler-utils (provides pdftotext and pdfinfo)
# On macOS with Homebrew:
brew install poppler

# On Ubuntu/Debian:
sudo apt-get install poppler-utils

# On CentOS/RHEL/Fedora:
sudo yum install poppler-utils    # CentOS/RHEL
sudo dnf install poppler-utils    # Fedora

# Install anystyle (requires Ruby)
gem install anystyle-cli
```

### Install pdfsources

```bash
uv pip install pdfsources
```

## Usage

The `pdfsources` command extracts and processes citations from PDF files to generate formatted bibliographies.

```bash
pdfsources [OPTIONS] [INPUT_FILES...]
```

### Default Behavior

**By default, `pdfsources` automatically processes PDF files:**

1. **Scans for PDFs**: Looks for PDF files in a `pdfs/` directory in the current working directory
2. **Extracts Citations**: Processes found PDFs with `anystyle` to extract citation data
3. **Generates ALL Bibliography Formats**: Creates three different bibliography files

Simply run:
```bash
pdfsources
```

This will process all PDF files in the `pdfs/` directory and generate:
- `bibliography_divided.md` - Citations grouped by type (books, articles, etc.)
- `bibliography_combined.md` - Single alphabetical list of all citations  
- `bibliography_sources.md` - Citations grouped by source PDF file

### Options

*   `--divided-output`: Generate a bibliography divided by type (e.g., books, articles). Output: `bibliography_divided.md`
*   `--combined-output`: Generate a single combined bibliography with all sources. Output: `bibliography_combined.md`
*   `--sources-output`: Generate a bibliography grouped by the original PDF source file. Output: `bibliography_sources.md`
*   `--output <filename>`: Specify a custom output file name (overridden by specific output flags)
*   `--style <style>`: Choose the citation style: `chicago` (default), `apa`, `harvard`
*   `-d`, `--debug`: Enable debug logging for verbose output
*   `INPUT_FILES...`: Specify JSON files directly (bypasses PDF scanning)

### Examples

**Process PDFs in the current directory (generates all 3 formats):**
```bash
# Create pdfs/ directory and add PDF files
mkdir pdfs
cp *.pdf pdfs/
pdfsources                                 # Creates all 3 bibliography files
```

**Generate specific output formats:**
```bash
pdfsources --divided-output --style apa    # Only bibliography by type in APA style
pdfsources --combined-output               # Only single combined bibliography
pdfsources --sources-output                # Only bibliography grouped by source PDF
```

**Process specific JSON files directly:**
```bash
pdfsources info/citations1.json info/citations2.json
pdfsources --style harvard existing-citations.json
```

## System Requirements

- **Python 3.8+**
- **Ruby** (for anystyle)
- **poppler-utils** (provides `pdftotext` and `pdfinfo` - required by anystyle)
- **anystyle-cli gem** (the core citation extraction engine)

If you encounter issues with PDF processing, ensure all dependencies are properly installed:
```bash
anystyle --version    # Should show version number
pdftotext -v         # Should show poppler version
pdfinfo -v           # Should show poppler version
```
