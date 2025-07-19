"""Bibliography output writers."""

import json
import logging
import os
from collections import defaultdict
from typing import List, Dict, Any
from .models import Citation
from .formatters.base import BaseFormatter

logger = logging.getLogger(__name__)


def parse_citation(citation_data: Dict[str, Any]) -> Citation:
    """Parse citation data into a Citation object."""
    try:
        return Citation(**citation_data)
    except Exception as e:
        logger.warning(f"Failed to parse citation: {e}")
        return Citation()


class BibliographyWriter:
    """Handles writing bibliographies in different formats."""
    
    def __init__(self, formatter: BaseFormatter):
        self.formatter = formatter
    
    def load_citations_from_files(self, json_files: List[str]) -> List[Citation]:
        """Load and parse citations from JSON files."""
        all_citations = []
        
        for file_name in json_files:
            try:
                with open(file_name, 'r', encoding='utf-8') as json_file:
                    data = json.load(json_file)
                    if isinstance(data, list):
                        for item in data:
                            citation = parse_citation(item)
                            if citation.has_valid_content():
                                all_citations.append(citation)
                    else:
                        logger.warning(f"Expected list in {file_name}, got {type(data)}")
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Error reading {file_name}: {e}")
        
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