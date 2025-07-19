import json
import os
import argparse
import logging
from collections import defaultdict
import toml
from platformdirs import user_config_dir
import sys
import subprocess
import glob
from typing import List, Dict, Any
from pydantic import ValidationError
import importlib.metadata
from pathlib import Path

from .models import Citation, Person

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Get version from package metadata
def get_version():
    try:
        return importlib.metadata.version("pdfsources")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"

__version__ = get_version()

# Security functions
def escape_markdown(text):
    """Escape markdown special characters to prevent injection."""
    if not isinstance(text, str):
        return text
    # Escape markdown special characters
    escape_chars = ['[', ']', '(', ')', '*', '_', '`', '#', '\\']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

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

# Configuration management
APP_NAME = "pdfsources"
CONFIG_FILE_NAME = "config.toml"

def get_config_path():
    return os.path.join(user_config_dir(APP_NAME), CONFIG_FILE_NAME)

def load_config():
    config_path = get_config_path()
    default_config = {
        "output": {
            "default_output_file": "bibliography.md",
            "default_style": "chicago"
        }
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = toml.load(f)
            # Merge with defaults to ensure all keys are present
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
                elif isinstance(value, dict) and isinstance(config[key], dict):
                    for sub_key, sub_value in value.items():
                        if sub_key not in config[key]:
                            config[key][sub_key] = sub_value
            return config
        except Exception as e:
            logger.warning(f"Error loading config file {config_path}: {e}. Using default configuration.")
            return default_config
    else:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            toml.dump(default_config, f)
        return default_config

def check_anystyle_available() -> bool:
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

def find_pdfs_in_directory(pdf_dir="pdfs"):
    """Find all PDF files in the specified directory."""
    if not os.path.exists(pdf_dir):
        return []
    
    pdf_patterns = [
        os.path.join(pdf_dir, "*.pdf"),
        os.path.join(pdf_dir, "*.PDF")
    ]
    
    pdf_files = []
    for pattern in pdf_patterns:
        pdf_files.extend(glob.glob(pattern))
    
    return sorted(pdf_files)

def process_pdfs_with_anystyle(pdf_files, output_dir="info"):
    """Process PDF files using anystyle to extract citations."""
    if not pdf_files:
        return []
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    json_files = []
    for pdf_file in pdf_files:
        # Generate output filename based on PDF name
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
                with open(safe_json_output, 'w') as f:
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
            logger.error("Ensure Ruby is installed and anystyle is in your PATH")
            break
        except Exception as e:
            logger.warning(f"Error processing {pdf_file}: {e}")
    
    return json_files

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

def get_default_input_files():
    """Get default input files by checking for PDFs and existing JSON files."""
    # First, check if there are PDFs to process
    pdf_files = find_pdfs_in_directory()
    
    if pdf_files:
        logger.info(f"Found {len(pdf_files)} PDF files in 'pdfs/' directory")
        
        # Check if anystyle is available before attempting to process PDFs
        if not check_anystyle_available():
            logger.error("anystyle command not found! Cannot process PDF files.")
            logger.error("Please install required dependencies:")
            logger.error("  1. poppler-utils: brew install poppler (macOS) or apt-get install poppler-utils (Ubuntu)")
            logger.error("  2. anystyle: gem install anystyle-cli")
            logger.error("Ensure Ruby is installed and anystyle is in your PATH")
            logger.info("Falling back to looking for existing JSON files...")
        else:
            # Process PDFs with anystyle
            json_files = process_pdfs_with_anystyle(pdf_files)
            if json_files:
                return json_files
    
    # Fall back to looking for existing JSON files
    fallback_files = [
        'info/anystyle-report-full.json',
        'anystyle-report-full.json'
    ]
    
    for file in fallback_files:
        if os.path.exists(file):
            logger.info(f"Using existing JSON file: {file}")
            return [file]
    
    # If no PDFs and no existing JSON files, return empty list
    logger.warning("No PDF files found in 'pdfs/' directory and no existing JSON files found")
    return []

def get_author_string(authors: List[Person], editors: List[Person] = None) -> str:
    """Creates a formatted string of authors or editors."""
    if not authors and not editors:
        return ""

    items = authors if authors else editors
    names = []
    for person in items:
        if isinstance(person, dict):
            # Handle raw dict input (backwards compatibility)
            person = Person(**person)
        
        if person.family and person.given:
            names.append(f"{escape_markdown(person.family)}, {escape_markdown(person.given)}")
        elif person.family:
            names.append(escape_markdown(person.family))
    
    if not names:
        return ""

    if len(names) > 1:
        author_string = f"{', '.join(names[:-1])}, and {names[-1]}"
    else:
        author_string = names[0]

    if editors:
        author_string += ", eds."
        
    return author_string

def get_first_item(ref, key):
    """Safely gets the first item from a list in a reference, or an empty string."""
    items = ref.get(key, [])
    if items and isinstance(items, list):
        return items[0].strip()
    return ""

def infer_type(ref):
    """Infers the reference type based on available fields."""
    ref_type = ref.get('type')
    if ref_type and isinstance(ref_type, list):
        ref_type = ref_type[0]

    if ref_type:
        return ref_type
    if 'container-title' in ref:
        return 'article-journal'
    if 'publisher' in ref or 'location' in ref:
        return 'book'
    return 'generic'

def format_chicago(citation: Citation) -> str:
    """Formats a single citation into a Chicago-style bibliography entry."""
    logger.debug(f"Processing reference: {citation.title}")
    
    if not citation.has_valid_content():
        return ""
    
    entry_parts = []

    # Authors or editors
    author_string = get_author_string(citation.author or [], citation.editor or [])
    if author_string:
        entry_parts.append(author_string + ".")

    # Title formatting based on type
    ref_type = citation.get_inferred_type()
    escaped_title = escape_markdown(citation.title)
    if ref_type.value == 'book':
        entry_parts.append(f"*{escaped_title}*.")
    else:
        entry_parts.append(f'"{escaped_title}".')

    # Container title (journal, book series, etc.)
    if citation.container_title:
        entry_parts.append(f"*{escape_markdown(citation.container_title)}*")

    # Volume
    if citation.volume:
        entry_parts.append(f"{citation.volume}")

    # Issue
    if citation.issue:
        entry_parts.append(f", no. {citation.issue}")

    # Date
    if citation.date:
        entry_parts.append(f"({citation.date})")

    # Pages
    if citation.pages:
        entry_parts.append(f": {citation.pages}")

    # Publisher and location
    if escape_markdown(citation.location) and escape_markdown(citation.publisher):
        entry_parts.append(f"{escape_markdown(citation.location)}: {escape_markdown(citation.publisher)}, {citation.date}.")
    elif escape_markdown(citation.publisher) and citation.date:
        entry_parts.append(f"{escape_markdown(citation.publisher)}, {citation.date}.")
    elif escape_markdown(citation.location) and citation.date:
        entry_parts.append(f"{escape_markdown(citation.location)}, {citation.date}.")

    final_entry = " ".join(filter(None, entry_parts)).replace("..", ".").strip()
    return final_entry

def parse_citation(raw_data: Dict[str, Any]) -> Citation:
    """Parse raw citation data into a validated Citation model."""
    try:
        # Convert author/editor dicts to Person models if they exist
        if 'author' in raw_data and raw_data['author']:
            raw_data['author'] = [Person(**author) if isinstance(author, dict) else author 
                                 for author in raw_data['author']]
        
        if 'editor' in raw_data and raw_data['editor']:
            raw_data['editor'] = [Person(**editor) if isinstance(editor, dict) else editor 
                                 for editor in raw_data['editor']]
        
        return Citation(**raw_data)
    except ValidationError as e:
        logger.warning(f"Failed to validate citation: {e}")
        # Return a minimal citation with just the raw data
        return Citation(title=str(raw_data.get('title', 'Unknown Title')))

def format_apa(citation: Citation):
    """Formats a single reference into an APA-style bibliography entry."""
    logger.debug(f"Processing reference: {citation.title}")
    
    if not citation.has_valid_content():
        return ""
        
    entry_parts = []

    author_string = get_author_string(citation.author or [], citation.editor or [])
    if author_string:
        entry_parts.append(author_string)

    if citation.date:
        entry_parts.append(f"({citation.date}).")

    if not citation.title:
        return ""
    entry_parts.append(escape_markdown(citation.title))

    if citation.container_title:
        entry_parts.append(f"*{escape_markdown(citation.container_title)}*")

    if citation.volume:
        entry_parts.append(f", *{citation.volume}*")

    if citation.issue:
        entry_parts.append(f"({citation.issue})")
    
    if citation.pages:
        entry_parts.append(f", {citation.pages}")

    if escape_markdown(citation.publisher):
        if escape_markdown(citation.location):
            entry_parts.append(f"{escape_markdown(citation.location)}: {escape_markdown(citation.publisher)}.")
        else:
            entry_parts.append(f"{escape_markdown(citation.publisher)}.")

    final_entry = " ".join(filter(None, entry_parts)).replace("..", ".").strip()
    return final_entry

def format_harvard(citation: Citation):
    """Formats a single reference into a Harvard-style bibliography entry."""
    logger.debug(f"Processing reference: {citation.title}")
    
    if not citation.has_valid_content():
        return ""
        
    entry_parts = []

    author_string = get_author_string(citation.author or [], citation.editor or [])
    if author_string:
        entry_parts.append(author_string)

    if citation.date:
        entry_parts.append(f"{citation.date},")

    if not citation.title:
        return ""
    entry_parts.append(f"*{escape_markdown(citation.title)}*.")
    
    if escape_markdown(citation.publisher):
        if escape_markdown(citation.location):
            entry_parts.append(f"{escape_markdown(citation.location)}: {escape_markdown(citation.publisher)}.")
        else:
            entry_parts.append(f"{escape_markdown(citation.publisher)}.")

    final_entry = " ".join(filter(None, entry_parts)).replace("..", ".").strip()
    return final_entry

def process_files(json_files, output_file, individual_files=False, style='chicago', output_type='divided'):
    """Processes a list of JSON files and writes the output to a file."""
    
    formatters = {
        'chicago': format_chicago,
        'apa': format_apa,
        'harvard': format_harvard,
    }
    formatter = formatters.get(style, format_chicago)

    with open(output_file, 'w') as f:
        if output_type == 'divided':
            f.write(f"# Bibliography ({style.capitalize()})\n\n")
            all_refs = []
            for file_name in json_files:
                if os.path.getsize(file_name) > 0:
                    with open(file_name, 'r') as json_file:
                        try:
                            data = json.load(json_file)
                            if isinstance(data, list):
                                all_refs.extend(data)
                            elif isinstance(data, dict):
                                all_refs.append(data)
                        except json.JSONDecodeError:
                            logger.warning(f"Could not decode JSON from {file_name}")
            
            logger.debug(f"Processing {len(all_refs)} references for combined bibliography.")
            
            grouped_refs = defaultdict(list)
            for ref in all_refs:
                citation = parse_citation(ref)
                ref_type = citation.get_inferred_type().value
                formatted_entry = formatter(citation)
                if formatted_entry:
                    grouped_refs[ref_type].append(formatted_entry)

            for ref_type, refs in grouped_refs.items():
                f.write(f"## {ref_type.replace('-', ' ').title()}\n\n")
                refs.sort(key=lambda x: x.split(',')[0].lower() if x.split(',')[0] else x)
                for entry in refs:
                    f.write(f"* {entry}\n")
                f.write("\n")

        elif output_type == 'combined':
            f.write(f"# Bibliography ({style.capitalize()})\n\n")
            all_refs = []
            for file_name in json_files:
                if os.path.getsize(file_name) > 0:
                    with open(file_name, 'r') as json_file:
                        try:
                            data = json.load(json_file)
                            if isinstance(data, list):
                                all_refs.extend(data)
                            elif isinstance(data, dict):
                                all_refs.append(data)
                        except json.JSONDecodeError:
                            logger.warning(f"Could not decode JSON from {file_name}")
            
            logger.debug(f"Processing {len(all_refs)} references for combined bibliography.")
            bibliography = []
            for ref in all_refs:
                citation = parse_citation(ref)
                formatted_entry = formatter(citation)
                if formatted_entry:
                    bibliography.append(formatted_entry)
                else:
                    logger.debug(f"Skipping malformed reference: {citation.title or 'Unknown'}")
            bibliography.sort(key=lambda x: x.split(',')[0].lower() if x.split(',')[0] else x)
            logger.debug(f"Generated {len(bibliography)} entries for combined bibliography.")
            
            for entry in bibliography:
                f.write(f"* {entry}\n")

        elif output_type == 'sources':
            f.write(f"# Bibliography by Source ({style.capitalize()})\n\n")
            for file_name in json_files:
                source_name = os.path.basename(file_name).replace('.json', '').replace('_', ' ').title()
                if os.path.getsize(file_name) > 0:
                    with open(file_name, 'r') as json_file:
                        try:
                            refs = json.load(json_file)
                            logger.debug(f"Processing {len(refs)} references for {file_name}.")
                            bibliography = []
                            for ref in refs:
                                citation = parse_citation(ref)
                                formatted_entry = formatter(citation)
                                if formatted_entry:
                                    bibliography.append(formatted_entry)
                                else:
                                    logger.debug(f"Skipping malformed reference in {file_name}: {citation.title or 'Unknown'}")
                            bibliography.sort(key=lambda x: x.split(',')[0].lower() if x.split(',')[0] else x)
                            logger.debug(f"Generated {len(bibliography)} entries for {file_name}.")
                            
                            # Write header with count
                            f.write(f"## {source_name} ({len(bibliography)} sources)\n\n")
                            for entry in bibliography:
                                f.write(f"* {entry}\n")
                        except json.JSONDecodeError:
                            logger.warning(f"Could not decode JSON from {file_name}")
                            f.write(f"## {source_name} (0 sources)\n\n")
                else:
                    f.write(f"## {source_name} (0 sources)\n\n")
                f.write("\n")

        elif output_type == 'sources_divided':
            f.write(f"# Bibliography by Source with Categories ({style.capitalize()})\n\n")
            for file_name in json_files:
                source_name = os.path.basename(file_name).replace('.json', '').replace('_', ' ').title()
                if os.path.getsize(file_name) > 0:
                    with open(file_name, 'r') as json_file:
                        try:
                            refs = json.load(json_file)
                            logger.debug(f"Processing {len(refs)} references for {file_name}.")
                            
                            # Group citations by type
                            grouped_refs = defaultdict(list)
                            total_valid = 0
                            for ref in refs:
                                citation = parse_citation(ref)
                                ref_type = citation.get_inferred_type().value
                                formatted_entry = formatter(citation)
                                if formatted_entry:
                                    grouped_refs[ref_type].append(formatted_entry)
                                    total_valid += 1
                                else:
                                    logger.debug(f"Skipping malformed reference in {file_name}: {citation.title or 'Unknown'}")
                            
                            # Write header with count
                            f.write(f"## {source_name} ({total_valid} sources)\n\n")
                            
                            # Write each category
                            for ref_type, entries in grouped_refs.items():
                                f.write(f"### {ref_type.replace('-', ' ').title()}\n\n")
                                entries.sort(key=lambda x: x.split(',')[0].lower() if x.split(',')[0] else x)
                                for entry in entries:
                                    f.write(f"* {entry}\n")
                                f.write("\n")
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Could not decode JSON from {file_name}")
                            f.write(f"## {source_name} (0 sources)\n\n")
                else:
                    f.write(f"## {source_name} (0 sources)\n\n")
                f.write("\n")

def main():
    """Main function to process the citation files."""
    
    parser = argparse.ArgumentParser(
        description="Extract and process citations from PDF files. By default, scans 'pdfs/' directory for PDF files and processes them with anystyle. Requires 'anystyle' gem to be installed (gem install anystyle-cli).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
**Default Behavior:**
If no input files are specified, pdfsources will:
1. Look for PDF files in the 'pdfs/' directory in the current working directory
2. Process found PDFs with anystyle to extract citations 
3. Generate ALL bibliography formats: divided, combined, sources, and sources divided

If no output type is specified, generates all four files:
- bibliography_divided.md (citations grouped by type)
- bibliography_combined.md (single alphabetical list)  
- bibliography_sources.md (grouped by source PDF)
- bibliography_sources_divided.md (sources with categories)

**Examples:**
  pdfsources                           # Process PDFs, generate all 4 formats
  pdfsources --combined-output         # Generate only combined bibliography
  pdfsources input.json                # Process JSON file, generate all 4 formats
  pdfsources --style apa *.json        # Process JSON files with APA style, all formats
        """
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--divided-output", action="store_true", help="Generate bibliography divided by type (default: bibliography_divided.md).")
    parser.add_argument("--combined-output", action="store_true", help="Generate combined bibliography (output: bibliography_combined.md).")
    parser.add_argument("--sources-output", action="store_true", help="Generate bibliography grouped by source PDF (output: bibliography_sources.md).")
    parser.add_argument("--sources-divided-output", action="store_true", help="Generate bibliography grouped by source PDF with categories (output: bibliography_sources_divided.md).")
    parser.add_argument("--output", help="Output file name (overridden by specific output flags).")
    parser.add_argument("--style", choices=['chicago', 'apa', 'harvard'], help="Citation style (default: chicago).")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing files without prompting.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite any existing bibliography files without prompting.")
    parser.add_argument("--no-interaction", action="store_true", help="Disable interactive prompts (fail if files exist).")
    parser.add_argument("input_files", nargs='*', help="Input JSON file(s). If not specified, scans 'pdfs/' directory for PDF files to process.")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled.")
    
    config = load_config()

    # Determine input files
    if args.input_files:
        input_files = args.input_files
        logger.info(f"Using specified input files: {input_files}")
    else:
        input_files = get_default_input_files()
        if not input_files:
            logger.error("No input files found. Place PDF files in 'pdfs/' directory or specify JSON files as arguments.")
            sys.exit(1)

    style = args.style if args.style else config["output"]["default_style"]

    # Determine which output types to generate
    output_types_specified = any([args.combined_output, args.sources_output, args.divided_output, args.sources_divided_output])
    
    if output_types_specified:
        # Generate only the specified type
        if args.combined_output:
            output_file = "bibliography_combined.md"
            output_type = 'combined'
        elif args.sources_output:
            output_file = "bibliography_sources.md"
            output_type = 'sources'
        elif args.sources_divided_output:
            output_file = "bibliography_sources_divided.md"
            output_type = 'sources_divided'
        elif args.divided_output:
            output_file = "bibliography_divided.md"
            output_type = 'divided'
        
        # Use custom output filename if specified
        if args.output:
            output_file = args.output
        
        # Check for existing file and get safe filename
        safe_output_file = get_safe_output_filename(output_file, args.force or args.overwrite, args.no_interaction)
        process_files(input_files, safe_output_file, False, style, output_type)
        logger.info(f"Generated bibliography: {safe_output_file}")
    else:
        # Default behavior: generate all four types
        logger.info("No specific output type specified. Generating all bibliography formats...")
        
        # Generate divided bibliography
        safe_divided_file = get_safe_output_filename("bibliography_divided.md", args.force or args.overwrite, args.no_interaction)
        process_files(input_files, safe_divided_file, False, style, 'divided')
        logger.info(f"Generated {safe_divided_file}")
        
        # Generate combined bibliography  
        safe_combined_file = get_safe_output_filename("bibliography_combined.md", args.force or args.overwrite, args.no_interaction)
        process_files(input_files, safe_combined_file, False, style, 'combined')
        logger.info(f"Generated {safe_combined_file}")
        
        # Generate sources bibliography
        safe_sources_file = get_safe_output_filename("bibliography_sources.md", args.force or args.overwrite, args.no_interaction)
        process_files(input_files, safe_sources_file, False, style, 'sources')
        logger.info(f"Generated {safe_sources_file}")
        
        # Generate sources divided bibliography
        safe_sources_divided_file = get_safe_output_filename("bibliography_sources_divided.md", args.force or args.overwrite, args.no_interaction)
        process_files(input_files, safe_sources_divided_file, False, style, 'sources_divided')
        logger.info(f"Generated {safe_sources_divided_file}")

if __name__ == "__main__":
    main()