"""APA citation formatter."""

import logging
from .base import BaseFormatter, escape_markdown, get_author_string
from ..models import Citation

logger = logging.getLogger(__name__)


class APAFormatter(BaseFormatter):
    """APA style citation formatter."""
    
    @property
    def style_name(self) -> str:
        return "apa"
    
    def format(self, citation: Citation) -> str:
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
            entry_parts.append(f", {citation.pages}.")

        if citation.publisher:
            if citation.location:
                entry_parts.append(f"{escape_markdown(citation.location)}: {escape_markdown(citation.publisher)}.")
            else:
                entry_parts.append(f"{escape_markdown(citation.publisher)}.")

        final_entry = " ".join(filter(None, entry_parts)).replace("..", ".").strip()
        return final_entry