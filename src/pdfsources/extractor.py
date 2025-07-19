"""PDF citation extraction using anystyle."""

import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def validate_file_path(file_path):
    """Validate and normalize file paths to prevent path traversal attacks."""
    try:
        path = Path(file_path).resolve()
        # Ensure the path is within allowed boundaries (current working directory or subdirectories)
        cwd = Path.cwd().resolve()
        path.relative_to(cwd)
        return str(path)
    except (ValueError, OSError):
        raise ValueError(f"Invalid or unsafe file path: {file_path}")


def check_anystyle_available():
    """Check if anystyle command is available."""
    try:
        result = subprocess.run(["anystyle", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.debug(f"anystyle version: {result.stdout.strip()}")
            return True
        else:
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def extract_citations_from_pdfs(pdf_files, output_dir="info"):
    """Extract citations from PDF files using anystyle."""
    if not check_anystyle_available():
        logger.error("anystyle command not found!")
        logger.error("Please install required dependencies:")
        logger.error("  1. poppler-utils: brew install poppler (macOS) or apt-get install poppler-utils (Ubuntu)")
        logger.error("  2. anystyle: gem install anystyle-cli")
        return []
    
    if not pdf_files:
        logger.info("No PDF files found to process")
        return []
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    json_files = []
    for pdf_file in pdf_files:
        # Generate output filename
        pdf_basename = os.path.splitext(os.path.basename(pdf_file))[0]
        json_output = os.path.join(output_dir, f"anystyle-{pdf_basename}.json")
        
        logger.info(f"Processing {pdf_file} -> {json_output}")
        
        try:
            # Validate file paths before subprocess call
            safe_pdf_file = validate_file_path(pdf_file)
            safe_json_output = validate_file_path(json_output)
            
            # Run anystyle command
            result = subprocess.run([
                "anystyle", "-f", "json", "find", safe_pdf_file
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and result.stdout.strip():
                # Write JSON output
                with open(safe_json_output, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                json_files.append(safe_json_output)
                logger.debug(f"Successfully processed {pdf_file}")
            else:
                logger.warning(f"Failed to process {pdf_file}: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout processing {pdf_file}")
        except FileNotFoundError:
            logger.error("anystyle command not found!")
            logger.error("Please install required dependencies:")
            logger.error("  1. poppler-utils: brew install poppler (macOS) or apt-get install poppler-utils (Ubuntu)")
            logger.error("  2. anystyle: gem install anystyle-cli")
            break
        except Exception as e:
            logger.warning(f"Error processing {pdf_file}: {e}")
    
    return json_files