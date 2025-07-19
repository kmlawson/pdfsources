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
    
    print("Processing pdfs:")
    
    json_files = []
    failed_files = []
    
    for pdf_file in pdf_files:
        # Generate output filename
        pdf_basename = os.path.splitext(os.path.basename(pdf_file))[0]
        json_output = os.path.join(output_dir, f"anystyle-{pdf_basename}.json")
        
        # Truncate long filenames for display
        display_name = pdf_basename
        if len(display_name) > 50:
            display_name = display_name[:47] + "..."
        
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
                
                # Count citations by type
                citation_counts = _count_citations_by_type(result.stdout)
                total_sources = sum(citation_counts.values())
                
                if total_sources > 0:
                    count_parts = []
                    if citation_counts.get('books', 0) > 0:
                        count_parts.append(f"{citation_counts['books']} books")
                    if citation_counts.get('articles', 0) > 0:
                        count_parts.append(f"{citation_counts['articles']} articles")
                    if citation_counts.get('other', 0) > 0:
                        count_parts.append(f"{citation_counts['other']} other")
                    
                    count_str = ", ".join(count_parts)
                    print(f"- {display_name}: {total_sources} sources found ({count_str})")
                    json_files.append(safe_json_output)
                else:
                    print(f"- {display_name}: no sources found")
                    
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                diagnostics = _diagnose_pdf_failure(safe_pdf_file, error_msg)
                failed_files.append((display_name, f"anystyle error: {error_msg}", diagnostics))
                
        except subprocess.TimeoutExpired:
            diagnostics = _diagnose_pdf_failure(safe_pdf_file, "timeout")
            failed_files.append((display_name, "Processing timeout (>5 minutes)", diagnostics))
        except FileNotFoundError:
            logger.error("anystyle command not found!")
            logger.error("Please install required dependencies:")
            logger.error("  1. poppler-utils: brew install poppler (macOS) or apt-get install poppler-utils (Ubuntu)")
            logger.error("  2. anystyle: gem install anystyle-cli")
            break
        except Exception as e:
            diagnostics = _diagnose_pdf_failure(safe_pdf_file, str(e))
            failed_files.append((display_name, f"System error: {str(e)}", diagnostics))
    
    # Report failed files
    if failed_files:
        print("\nFailed to process:")
        for item in failed_files:
            if len(item) == 3:  # New format with diagnostics
                filename, error, diagnostics = item
                print(f"- {filename}")
                print(f"  Error: {error}")
                if diagnostics:
                    print("  Diagnostics:")
                    for diagnostic in diagnostics:
                        print(f"    - {diagnostic}")
            else:  # Legacy format without diagnostics
                filename, error = item
                print(f"- {filename}")
                print(f"  Error: {error}")
    
    return json_files


def _diagnose_pdf_failure(pdf_file, error_msg):
    """Diagnose specific issues with failed PDF processing."""
    diagnostics = []
    
    try:
        # Check if file exists and is readable
        if not os.path.exists(pdf_file):
            diagnostics.append("File does not exist")
            return diagnostics
        
        if not os.access(pdf_file, os.R_OK):
            diagnostics.append("File is not readable (permission issue)")
            return diagnostics
        
        # Check file size
        file_size = os.path.getsize(pdf_file)
        if file_size == 0:
            diagnostics.append("File is empty (0 bytes)")
        elif file_size < 1024:  # Less than 1KB
            diagnostics.append(f"File is very small ({file_size} bytes) - may be corrupted")
        
        # Check if it's actually a PDF by reading header
        try:
            with open(pdf_file, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    diagnostics.append("File is not a valid PDF (missing PDF header)")
        except Exception:
            diagnostics.append("Cannot read file header")
        
        # Test if pdftotext can process it (anystyle dependency)
        try:
            result = subprocess.run(
                ["pdftotext", "-l", "1", pdf_file, "-"], 
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                stderr_msg = result.stderr.strip() if result.stderr else "Unknown pdftotext error"
                diagnostics.append(f"pdftotext cannot process file: {stderr_msg}")
            elif not result.stdout.strip():
                diagnostics.append("PDF contains no extractable text (may be image-only)")
        except subprocess.TimeoutExpired:
            diagnostics.append("pdftotext timeout - file may be corrupted or very large")
        except FileNotFoundError:
            diagnostics.append("pdftotext not found - poppler-utils may not be installed")
        except Exception as e:
            diagnostics.append(f"pdftotext test failed: {str(e)}")
        
        # Test if pdfinfo can read metadata
        try:
            result = subprocess.run(
                ["pdfinfo", pdf_file], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                stderr_msg = result.stderr.strip() if result.stderr else "Unknown pdfinfo error"
                diagnostics.append(f"PDF metadata unreadable: {stderr_msg}")
        except subprocess.TimeoutExpired:
            diagnostics.append("pdfinfo timeout - file may be corrupted")
        except FileNotFoundError:
            diagnostics.append("pdfinfo not found - poppler-utils may not be installed")
        except Exception:
            pass  # pdfinfo failure is less critical
        
    except Exception as e:
        diagnostics.append(f"Diagnostic error: {str(e)}")
    
    return diagnostics


def _count_citations_by_type(json_data):
    """Count citations by type from JSON data."""
    import json as json_lib
    from .writers import parse_citation
    
    try:
        citations_data = json_lib.loads(json_data)
        if not isinstance(citations_data, list):
            return {'books': 0, 'articles': 0, 'other': 0}
        
        counts = {'books': 0, 'articles': 0, 'other': 0}
        
        for item in citations_data:
            citation = parse_citation(item)
            if citation.has_valid_content():
                citation_type = citation.get_inferred_type()
                if citation_type.value == 'book':
                    counts['books'] += 1
                elif citation_type.value in ['article-journal', 'article-newspaper']:
                    counts['articles'] += 1
                else:
                    counts['other'] += 1
        
        return counts
    except Exception:
        return {'books': 0, 'articles': 0, 'other': 0}