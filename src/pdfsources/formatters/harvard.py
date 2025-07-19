"""Harvard citation formatter."""

import logging
from .base import BaseFormatter, escape_markdown, get_author_string
from ..models import Citation

logger = logging.getLogger(__name__)


class HarvardFormatter(BaseFormatter):
    """Harvard style citation formatter."""
    
    @property
    def style_name(self) -> str:
        return "harvard"
    
    def format(self, citation: Citation) -> str:
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
        
        if citation.publisher:
            if citation.location:
                entry_parts.append(f"{escape_markdown(citation.location)}: {escape_markdown(citation.publisher)}.")
            else:
                entry_parts.append(f"{escape_markdown(citation.publisher)}.")

        final_entry = " ".join(filter(None, entry_parts)).replace("..", ".").strip()
        return final_entry