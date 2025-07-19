"""Main application logic for pdfsources."""

import logging
from .cli import create_parser, configure_logging
from .config import load_config
from .discovery import find_pdfs_in_directory, get_safe_output_filename
from .extractor import extract_citations_from_pdfs
from .writers import BibliographyWriter
from .formatters import ChicagoFormatter, APAFormatter, HarvardFormatter

logger = logging.getLogger(__name__)


def get_formatter(style: str):
    """Get the appropriate formatter for the given style."""
    formatters = {
        'chicago': ChicagoFormatter(),
        'apa': APAFormatter(),
        'harvard': HarvardFormatter()
    }
    return formatters.get(style, ChicagoFormatter())


def main():
    """Main application entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Configure logging
    configure_logging(args.debug)
    
    # Load configuration
    config = load_config()
    
    # Determine citation style
    style = args.style or config["output"]["default_style"]
    formatter = get_formatter(style)
    writer = BibliographyWriter(formatter)
    
    # Determine input files
    if args.input_files:
        # Use provided JSON files directly
        input_files = args.input_files
        logger.info(f"Processing {len(input_files)} provided JSON files...")
    else:
        # Scan for PDFs and extract citations
        logger.info("Scanning for PDF files in 'pdfs/' directory...")
        pdf_files = find_pdfs_in_directory()
        
        if not pdf_files:
            logger.error("No PDF files found in 'pdfs/' directory")
            logger.info("Please add PDF files to the 'pdfs/' directory or specify JSON files directly")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        input_files = extract_citations_from_pdfs(pdf_files)
        
        if not input_files:
            logger.error("Failed to extract citations from PDF files")
            return
    
    # Determine output types to generate
    output_types = []
    if args.divided_output:
        output_types.append('divided')
    if args.combined_output:
        output_types.append('combined')
    if args.sources_output:
        output_types.append('sources')
    if args.sources_divided_output:
        output_types.append('sources_divided')
    
    # If no specific output type specified, generate all types
    if not output_types:
        output_types = ['divided', 'combined', 'sources', 'sources_divided']
        logger.info("No specific output type specified. Generating all bibliography formats...")
    
    # Generate bibliographies
    force_overwrite = args.force or args.overwrite
    
    for output_type in output_types:
        if output_type == 'divided':
            output_file = args.output if args.output and len(output_types) == 1 else "bibliography_divided.md"
            safe_output_file = get_safe_output_filename(output_file, force_overwrite, args.no_interaction)
            writer.write_divided_bibliography(safe_output_file, input_files)
            logger.info(f"Generated {safe_output_file}")
            
        elif output_type == 'combined':
            output_file = args.output if args.output and len(output_types) == 1 else "bibliography_combined.md"
            safe_output_file = get_safe_output_filename(output_file, force_overwrite, args.no_interaction)
            writer.write_combined_bibliography(safe_output_file, input_files)
            logger.info(f"Generated {safe_output_file}")
            
        elif output_type == 'sources':
            output_file = args.output if args.output and len(output_types) == 1 else "bibliography_sources.md"
            safe_output_file = get_safe_output_filename(output_file, force_overwrite, args.no_interaction)
            writer.write_sources_bibliography(safe_output_file, input_files)
            logger.info(f"Generated {safe_output_file}")
            
        elif output_type == 'sources_divided':
            output_file = args.output if args.output and len(output_types) == 1 else "bibliography_sources_divided.md"
            safe_output_file = get_safe_output_filename(output_file, force_overwrite, args.no_interaction)
            writer.write_sources_divided_bibliography(safe_output_file, input_files)
            logger.info(f"Generated {safe_output_file}")


if __name__ == "__main__":
    main()