"""Chicago Manual of Style citation formatter."""

import logging
from .base import BaseFormatter, escape_markdown, get_author_string
from ..models import Citation

logger = logging.getLogger(__name__)


class ChicagoFormatter(BaseFormatter):
    """Chicago Manual of Style citation formatter."""
    
    @property
    def style_name(self) -> str:
        return "chicago"
    
    def format(self, citation: Citation) -> str:
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
            entry_parts.append(f"no. {citation.issue}")

        # Date
        if citation.date:
            entry_parts.append(f"({citation.date})")

        # Pages
        if citation.pages:
            entry_parts.append(f"{citation.pages}.")

        # Publisher information
        if citation.publisher:
            if citation.location:
                entry_parts.append(f"{escape_markdown(citation.location)}: {escape_markdown(citation.publisher)}")
            else:
                entry_parts.append(f"{escape_markdown(citation.publisher)}")

        # Final date for books if not already included
        if ref_type.value == 'book' and citation.date and f"({citation.date})" not in entry_parts:
            entry_parts.append(f"{citation.date}.")

        final_entry = " ".join(filter(None, entry_parts)).replace("..", ".").strip()
        return final_entry