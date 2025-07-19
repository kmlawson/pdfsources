"""Bibliography output writers."""

import json
import logging
import os
from collections import defaultdict
from typing import List, Dict, Any, Set
from .models import Citation
from .formatters.base import BaseFormatter

logger = logging.getLogger(__name__)


def get_citation_signature(citation: Citation) -> str:
    """Generate a normalized signature for duplicate detection."""
    # Simplified title: lowercase, alphanumeric only
    title_part = ''.join(c for c in str(citation.title or '').lower() if c.isalnum())
    
    # Simplified authors: first two authors' last names
    author_part = ''
    if citation.author:
        author_names = []
        for author in citation.author[:2]:  # Take first two authors
            if hasattr(author, 'family') and author.family:
                author_names.append(''.join(c for c in author.family.lower() if c.isalnum()))
        author_part = ''.join(sorted(author_names))
    
    # Include publication year if available
    year_part = ''.join(c for c in str(citation.date or '') if c.isdigit())[:4]  # First 4 digits
    
    return f"{title_part}{author_part}{year_part}"


def parse_citation(citation_data: Dict[str, Any]) -> Citation:
    """Parse citation data into a Citation object."""
    try:
        # Convert anystyle field names to our field names
        normalized_data = dict(citation_data)
        if 'container-title' in normalized_data:
            normalized_data['container_title'] = normalized_data.pop('container-title')
        
        return Citation(**normalized_data)
    except Exception as e:
        logger.warning(f"Failed to parse citation: {e}")
        return Citation()


class BibliographyWriter:
    """Handles writing bibliographies in different formats."""
    
    def __init__(self, formatter: BaseFormatter):
        self.formatter = formatter
    
    def load_citations_from_files(self, json_files: List[str], deduplicate: bool = True) -> List[Citation]:
        """Load and parse citations from JSON files with optional deduplication."""
        all_citations = []
        seen_signatures: Set[str] = set()
        duplicate_count = 0
        
        for file_name in json_files:
            try:
                with open(file_name, 'r', encoding='utf-8') as json_file:
                    data = json.load(json_file)
                    if isinstance(data, list):
                        for item in data:
                            citation = parse_citation(item)
                            if citation.has_valid_content():
                                if deduplicate:
                                    signature = get_citation_signature(citation)
                                    if signature and signature not in seen_signatures:
                                        seen_signatures.add(signature)
                                        all_citations.append(citation)
                                    else:
                                        duplicate_count += 1
                                else:
                                    all_citations.append(citation)
                    else:
                        logger.warning(f"Expected list in {file_name}, got {type(data)}")
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Error reading {file_name}: {e}")
        
        if deduplicate and duplicate_count > 0:
            logger.info(f"Removed {duplicate_count} duplicate citations")
        
        logger.info(f"Loaded {len(all_citations)} valid citations from {len(json_files)} files")
        return all_citations
    
    def write_divided_bibliography(self, output_file: str, json_files: List[str]):
        """Write bibliography divided by reference type."""
        citations = self.load_citations_from_files(json_files)
        
        # Group by type
        grouped_refs = defaultdict(list)
        for citation in citations:
            ref_type = citation.get_inferred_type().value
            formatted_entry = self.formatter.format(citation)
            if formatted_entry:
                grouped_refs[ref_type].append(formatted_entry)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Bibliography ({self.formatter.style_name.capitalize()})\n\n")
            
            for ref_type, refs in grouped_refs.items():
                f.write(f"## {ref_type.replace('-', ' ').title()}\n\n")
                refs.sort(key=lambda x: x.split(',')[0].lower() if x.split(',')[0] else x)
                for entry in refs:
                    f.write(f"* {entry}\n")
                f.write("\n")
    
    def write_combined_bibliography(self, output_file: str, json_files: List[str]):
        """Write single combined bibliography."""
        citations = self.load_citations_from_files(json_files)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Bibliography ({self.formatter.style_name.capitalize()})\n\n")
            all_refs = []
            
            for citation in citations:
                formatted_entry = self.formatter.format(citation)
                if formatted_entry:
                    all_refs.append(formatted_entry)
            
            # Sort alphabetically by first word (usually author's last name)
            all_refs.sort(key=lambda x: x.split(',')[0].lower() if x.split(',')[0] else x)
            
            for entry in all_refs:
                f.write(f"* {entry}\n")
    
    def write_sources_bibliography(self, output_file: str, json_files: List[str]):
        """Write bibliography grouped by source file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Bibliography by Source ({self.formatter.style_name.capitalize()})\n\n")
            
            for file_name in json_files:
                try:
                    with open(file_name, 'r', encoding='utf-8') as json_file:
                        data = json.load(json_file)
                        valid_citations = []
                        
                        if isinstance(data, list):
                            for item in data:
                                citation = parse_citation(item)
                                if citation.has_valid_content():
                                    formatted_entry = self.formatter.format(citation)
                                    if formatted_entry:
                                        valid_citations.append(formatted_entry)
                        
                        source_name = os.path.basename(file_name).replace('.json', '').replace('anystyle-', '')
                        source_name = source_name.replace('_', ' ').title()
                        
                        if valid_citations:
                            valid_citations.sort(key=lambda x: x.split(',')[0].lower() if x.split(',')[0] else x)
                            f.write(f"## {source_name} ({len(valid_citations)} sources)\n\n")
                            for entry in valid_citations:
                                f.write(f"* {entry}\n")
                        else:
                            f.write(f"## {source_name} (0 sources)\n\n")
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logger.warning(f"Error reading {file_name}: {e}")
                    source_name = file_name.replace('.json', '').replace('info/', '').replace('anystyle-', '')
                    f.write(f"## {source_name} (0 sources)\n\n")
                f.write("\n")
    
    def write_sources_divided_bibliography(self, output_file: str, json_files: List[str]):
        """Write bibliography grouped by source file with categories."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Bibliography by Source with Categories ({self.formatter.style_name.capitalize()})\n\n")
            
            for file_name in json_files:
                try:
                    with open(file_name, 'r', encoding='utf-8') as json_file:
                        data = json.load(json_file)
                        grouped_refs = defaultdict(list)
                        
                        if isinstance(data, list):
                            for item in data:
                                citation = parse_citation(item)
                                if citation.has_valid_content():
                                    ref_type = citation.get_inferred_type().value
                                    formatted_entry = self.formatter.format(citation)
                                    if formatted_entry:
                                        grouped_refs[ref_type].append(formatted_entry)
                        
                        source_name = os.path.basename(file_name).replace('.json', '').replace('anystyle-', '')
                        source_name = source_name.replace('_', ' ').title()
                        
                        total_valid = sum(len(refs) for refs in grouped_refs.values())
                        if grouped_refs:
                            f.write(f"## {source_name} ({total_valid} sources)\n\n")
                            
                            for ref_type, refs in grouped_refs.items():
                                f.write(f"### {ref_type.replace('-', ' ').title()}\n\n")
                                refs.sort(key=lambda x: x.split(',')[0].lower() if x.split(',')[0] else x)
                                for entry in refs:
                                    f.write(f"* {entry}\n")
                                f.write("\n")
                        else:
                            f.write(f"## {source_name} (0 sources)\n\n")
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logger.warning(f"Error reading {file_name}: {e}")
                    source_name = file_name.replace('.json', '').replace('info/', '').replace('anystyle-', '')
                    f.write(f"## {source_name} (0 sources)\n\n")
                f.write("\n")