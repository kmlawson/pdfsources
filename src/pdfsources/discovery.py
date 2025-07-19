"""File discovery and PDF scanning functionality."""

import os
import glob
import logging

logger = logging.getLogger(__name__)


def find_pdfs_in_directory(pdf_dir="pdfs"):
    """Find all PDF files in the specified directory."""
    if not os.path.exists(pdf_dir):
        return []
    
    pdf_files = []
    for ext in ['*.pdf', '*.PDF']:
        pdf_files.extend(glob.glob(os.path.join(pdf_dir, ext)))
    
    logger.debug(f"Found {len(pdf_files)} PDF files in {pdf_dir}")
    return pdf_files


def get_safe_output_filename(filename, force=False, no_interaction=False):
    """Get a safe output filename, checking for existing files and prompting user for confirmation."""
    if not os.path.exists(filename):
        return filename
    
    # If force flag is set, always overwrite
    if force:
        return filename
    
    # If no-interaction flag is set, fail if file exists
    if no_interaction:
        raise FileExistsError(f"File '{filename}' already exists and --no-interaction flag is set")
    
    # File exists, ask user for confirmation
    try:
        response = input(f"File '{filename}' already exists. Overwrite? [y/N]: ").strip().lower()
        if response in ['y', 'yes']:
            return filename
    except (EOFError, KeyboardInterrupt):
        # Handle non-interactive environments or Ctrl+C
        pass
    
    # Find a unique filename with _[number] suffix
    base_name, ext = os.path.splitext(filename)
    counter = 1
    while True:
        new_filename = f"{base_name}_{counter}{ext}"
        if not os.path.exists(new_filename):
            logger.info(f"Using alternative filename: {new_filename}")
            return new_filename
        counter += 1