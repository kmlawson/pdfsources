"""Base citation formatter class."""

import re
from abc import ABC, abstractmethod
from typing import List
from ..models import Citation, Person


def clean_extracted_text(text):
    """Clean text extracted from PDFs to remove common artifacts and encoding issues."""
    if not isinstance(text, str):
        return text
    
    # Remove double backslashes that are artifacts from PDF extraction
    text = text.replace('\\\\', '')
    
    # Fix common escaped characters from anystyle
    text = text.replace('\\(', '(').replace('\\)', ')')
    text = text.replace('\\[', '[').replace('\\]', ']')
    text = text.replace('\\"', '"').replace("\\'", "'")
    text = text.replace('\\{', '{').replace('\\}', '}')
    
    # Remove HTML entities that may have been introduced
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&amp;', '&').replace('&quot;', '"')
    
    # Clean up excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def normalize_author_case(text):
    """Normalize author name capitalization to Title Case."""
    if not isinstance(text, str):
        return text
    
    # Handle ALL CAPS names by converting to title case
    if text.isupper():
        text = text.title()
    
    # Fix common title case issues with particles and prefixes
    # Handle Dutch, German, and other particles
    particles = ['van', 'von', 'de', 'da', 'del', 'della', 'du', 'le', 'la', 'el', 'al', 'der']
    for particle in particles:
        # Replace standalone particles with lowercase version
        text = re.sub(rf'\b{particle.title()}\b', particle, text)
    
    # Special case for "Der" -> "de" (German/Dutch particle)
    text = re.sub(r'\bDer\b', 'de', text)
    
    # Handle Irish/Scottish prefixes
    text = re.sub(r'\bMc([A-Z])', r'Mc\1', text)
    text = re.sub(r'\bO\'([A-Z])', r"O'\1", text)
    
    return text


def escape_markdown(text):
    """Escape markdown special characters and HTML tags to prevent injection."""
    if not isinstance(text, str):
        return text
    
    # First clean the text from PDF extraction artifacts
    text = clean_extracted_text(text)
    
    # Escape HTML tags to prevent script injection
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    # Escape markdown special characters
    escape_chars = ['[', ']', '(', ')', '*', '_', '`', '#', '\\']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


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
            # Clean and normalize author names
            family = normalize_author_case(clean_extracted_text(person.family))
            given = normalize_author_case(clean_extracted_text(person.given))
            names.append(f"{escape_markdown(family)}, {escape_markdown(given)}")
        elif person.family:
            family = normalize_author_case(clean_extracted_text(person.family))
            names.append(escape_markdown(family))
    
    if not names:
        return ""

    if len(names) > 1:
        author_string = f"{', '.join(names[:-1])}, and {names[-1]}"
    else:
        author_string = names[0]

    if editors:
        author_string += ", eds."
        
    return author_string


class BaseFormatter(ABC):
    """Abstract base class for citation formatters."""
    
    @abstractmethod
    def format(self, citation: Citation) -> str:
        """Format a citation according to the style's rules."""
        pass
    
    @property
    @abstractmethod
    def style_name(self) -> str:
        """Return the name of this citation style."""
        pass