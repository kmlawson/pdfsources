"""Test helper functions for robust testing."""

import re
from typing import List, Dict


def validate_bibliography_structure(content: str, style: str = "chicago") -> Dict[str, bool]:
    """Validate bibliography structure using regex patterns instead of exact strings."""
    validation = {
        "has_header": False,
        "has_correct_style": False,
        "has_citations": False,
        "proper_formatting": False
    }
    
    # Check for main header
    header_pattern = r"^# Bibliography"
    validation["has_header"] = bool(re.search(header_pattern, content, re.MULTILINE))
    
    # Check for style in header
    style_pattern = rf"# Bibliography \({style.capitalize()}\)"
    validation["has_correct_style"] = bool(re.search(style_pattern, content, re.MULTILINE))
    
    # Check for citation entries (lines starting with *)
    citation_pattern = r"^\* .+$"
    citations = re.findall(citation_pattern, content, re.MULTILINE)
    validation["has_citations"] = len(citations) > 0
    
    # Check for proper formatting patterns
    author_pattern = r"\* [A-Z][a-z]+, [A-Z]\."
    validation["proper_formatting"] = bool(re.search(author_pattern, content))
    
    return validation


def validate_citation_fields(citation_text: str, expected_fields: List[str]) -> Dict[str, bool]:
    """Validate that a citation contains expected fields using semantic analysis."""
    validation = {}
    
    field_patterns = {
        "author": r"[A-Z][a-z]+, [A-Z]\.",
        "title": r'"[^"]+"|[*][^*]+[*]',
        "year": r"\(?\d{4}\)?",
        "publisher": r"[A-Z][a-zA-Z\s]+\.",
        "location": r"[A-Z][a-zA-Z\s]+:"
    }
    
    for field in expected_fields:
        if field in field_patterns:
            pattern = field_patterns[field]
            validation[field] = bool(re.search(pattern, citation_text))
        else:
            validation[field] = field.lower() in citation_text.lower()
    
    return validation


def validate_divided_bibliography(content: str) -> Dict[str, bool]:
    """Validate divided bibliography structure."""
    validation = {
        "has_sections": False,
        "has_book_section": False,
        "has_article_section": False,
        "sections_have_citations": False
    }
    
    # Check for section headers
    section_pattern = r"^## [A-Z][a-z\s]+$"
    sections = re.findall(section_pattern, content, re.MULTILINE)
    validation["has_sections"] = len(sections) > 0
    
    # Check for specific sections
    validation["has_book_section"] = bool(re.search(r"## Book", content))
    validation["has_article_section"] = bool(re.search(r"## Article", content))
    
    # Check that sections have citations following them
    section_with_citations = r"## [A-Z][a-z\s]+\n+(\* .+\n)+"
    validation["sections_have_citations"] = bool(re.search(section_with_citations, content))
    
    return validation


def validate_sources_bibliography(content: str, expected_sources: List[str] = None) -> Dict[str, bool]:
    """Validate sources bibliography structure."""
    validation = {
        "has_source_sections": False,
        "source_sections_have_counts": False,
        "has_expected_sources": False
    }
    
    # Check for source sections with citation counts
    source_pattern = r"## [^(]+\(\d+ sources\)"
    sources = re.findall(source_pattern, content)
    validation["has_source_sections"] = len(sources) > 0
    validation["source_sections_have_counts"] = all("sources)" in source for source in sources)
    
    # Check for expected sources if provided
    if expected_sources:
        found_sources = 0
        for expected_source in expected_sources:
            source_clean = expected_source.replace("_", " ").title()
            if source_clean in content:
                found_sources += 1
        validation["has_expected_sources"] = found_sources >= len(expected_sources) * 0.5  # At least 50% match
    
    return validation


def validate_markdown_safety(content: str) -> Dict[str, bool]:
    """Validate that content is safe from markdown injection."""
    validation = {
        "no_unescaped_brackets": True,
        "no_unescaped_links": True,
        "no_script_tags": True
    }
    
    # Check for unescaped markdown that could be injection
    unescaped_bracket_pattern = r"(?<!\\)\[.*?(?<!\\)\](?!\()"
    validation["no_unescaped_brackets"] = not bool(re.search(unescaped_bracket_pattern, content))
    
    # Check for potential link injection
    link_pattern = r"\[.*?\]\(.*?\)"
    validation["no_unescaped_links"] = not bool(re.search(link_pattern, content))
    
    # Check for script tags (shouldn't be in bibliography)
    script_pattern = r"<script.*?>.*?</script>"
    validation["no_script_tags"] = not bool(re.search(script_pattern, content, re.IGNORECASE | re.DOTALL))
    
    return validation


def extract_citation_components(citation_text: str) -> Dict[str, str]:
    """Extract components from a formatted citation for detailed testing."""
    components = {
        "author": "",
        "title": "",
        "year": "",
        "publisher": "",
        "location": ""
    }
    
    # Extract author (usually at beginning)
    author_match = re.search(r"^[^.]+\.", citation_text)
    if author_match:
        components["author"] = author_match.group().strip()
    
    # Extract title (between quotes or asterisks)
    title_match = re.search(r'"([^"]+)"|[*]([^*]+)[*]', citation_text)
    if title_match:
        components["title"] = (title_match.group(1) or title_match.group(2)).strip()
    
    # Extract year
    year_match = re.search(r"\((\d{4})\)|(\d{4})", citation_text)
    if year_match:
        components["year"] = (year_match.group(1) or year_match.group(2)).strip()
    
    # Extract publisher info
    pub_match = re.search(r"([A-Z][a-zA-Z\s]+): ([A-Z][a-zA-Z\s]+)", citation_text)
    if pub_match:
        components["location"] = pub_match.group(1).strip()
        components["publisher"] = pub_match.group(2).strip()
    
    return components