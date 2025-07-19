"""Base citation formatter class."""

from abc import ABC, abstractmethod
from typing import List
from ..models import Citation, Person


def escape_markdown(text):
    """Escape markdown special characters to prevent injection."""
    if not isinstance(text, str):
        return text
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