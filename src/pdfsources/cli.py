"""Command line interface for pdfsources."""

import argparse
import logging
import importlib.metadata

logger = logging.getLogger(__name__)


def get_version():
    """Get version from package metadata."""
    try:
        return importlib.metadata.version("pdfsources")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Extract and process citations from PDF files using anystyle",
        epilog="""
Examples:
  pdfsources                             # Process PDFs in 'pdfs/' directory, generate all formats
  pdfsources --divided-output            # Generate only divided bibliography
  pdfsources --combined-output           # Generate only combined bibliography  
  pdfsources --sources-output            # Generate only sources bibliography
  pdfsources --sources-divided-output    # Generate only sources divided bibliography
  pdfsources --style apa --overwrite     # Generate all formats in APA style, overwrite existing
  pdfsources *.json                      # Process specific JSON files
  pdfsources --style harvard *.json     # Process JSON files with Harvard style
  pdfsources --style apa *.json         # Process JSON files with APA style, all formats
        """
    )
    
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {get_version()}")
    
    # Output format flags
    parser.add_argument("--divided-output", action="store_true", 
                       help="Generate bibliography divided by type (default: bibliography_divided.md).")
    parser.add_argument("--combined-output", action="store_true", 
                       help="Generate combined bibliography (output: bibliography_combined.md).")
    parser.add_argument("--sources-output", action="store_true", 
                       help="Generate bibliography grouped by source PDF (output: bibliography_sources.md).")
    parser.add_argument("--sources-divided-output", action="store_true", 
                       help="Generate bibliography grouped by source PDF with categories (output: bibliography_sources_divided.md).")
    
    # Other options
    parser.add_argument("--output", help="Output file name (overridden by specific output flags).")
    parser.add_argument("--style", choices=['chicago', 'apa', 'harvard'], 
                       help="Citation style (default: chicago).")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument("--force", action="store_true", 
                       help="Force overwrite existing files without prompting.")
    parser.add_argument("--overwrite", action="store_true", 
                       help="Overwrite any existing bibliography files without prompting.")
    parser.add_argument("--no-interaction", action="store_true", 
                       help="Disable interactive prompts (fail if files exist).")
    
    # Positional arguments
    parser.add_argument("input_files", nargs='*', 
                       help="Input JSON file(s). If not specified, scans 'pdfs/' directory for PDF files to process.")
    
    return parser


def configure_logging(debug: bool = False):
    """Configure logging based on debug flag."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    logger.setLevel(level)