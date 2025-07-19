"""Pydantic models for citation data validation."""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class CitationType(str, Enum):
    """Supported citation types."""
    BOOK = "book"
    ARTICLE_JOURNAL = "article-journal"
    ARTICLE_NEWSPAPER = "article-newspaper"
    CHAPTER = "chapter"
    REPORT = "report"
    THESIS = "thesis"
    WEBPAGE = "webpage"
    OTHER = "other"  # Renamed from GENERIC and placed last


class Person(BaseModel):
    """Model for author/editor information."""
    family: Optional[str] = Field(None, description="Family name")
    given: Optional[str] = Field(None, description="Given name")
    
    @validator('family', 'given', pre=True)
    def clean_whitespace(cls, v):
        """Clean whitespace from name fields."""
        if isinstance(v, str):
            return v.strip()
        return v


class Citation(BaseModel):
    """Model for a single citation reference."""
    type: Optional[Union[str, List[str]]] = Field(None, description="Citation type")
    title: Optional[Union[str, List[str]]] = Field(None, description="Title of the work")
    author: Optional[List[Person]] = Field(default_factory=list, description="Authors")
    editor: Optional[List[Person]] = Field(default_factory=list, description="Editors")
    container_title: Optional[Union[str, List[str]]] = Field(None, description="Container title (journal, book, etc.)")
    volume: Optional[Union[str, List[str]]] = Field(None, description="Volume number")
    issue: Optional[Union[str, List[str]]] = Field(None, description="Issue number")
    pages: Optional[Union[str, List[str]]] = Field(None, description="Page numbers")
    date: Optional[Union[str, List[str]]] = Field(None, description="Publication date")
    publisher: Optional[Union[str, List[str]]] = Field(None, description="Publisher")
    location: Optional[Union[str, List[str]]] = Field(None, description="Publication location")
    
    class Config:
        """Pydantic configuration."""
        # Allow extra fields that might come from anystyle
        extra = "allow"
        
    @validator('type', pre=True)
    def normalize_type(cls, v):
        """Normalize type field to a single string."""
        if isinstance(v, list) and v:
            return v[0]
        return v
    
    @validator('title', 'container_title', 'volume', 'issue', 'pages', 'date', 'publisher', 'location', pre=True)
    def normalize_string_fields(cls, v):
        """Normalize string fields that might come as lists."""
        if isinstance(v, list) and v:
            return v[0].strip() if isinstance(v[0], str) else str(v[0])
        elif isinstance(v, str):
            return v.strip()
        return v
    
    def get_inferred_type(self) -> CitationType:
        """Infer citation type based on available fields with enhanced heuristics."""
        if self.type:
            # Try to match known types
            type_str = self.type.lower() if isinstance(self.type, str) else str(self.type).lower()
            for ct in CitationType:
                if ct.value in type_str:
                    return ct
        
        # Enhanced heuristic-based inference
        title_str = str(self.title or '').lower()
        publisher_str = str(self.publisher or '').lower()
        container_str = str(self.container_title or '').lower()
        
        # Check for journal articles first
        if self.container_title:
            # Look for journal indicators
            journal_indicators = ['journal', 'review', 'proceedings', 'quarterly', 'annual']
            if any(indicator in container_str for indicator in journal_indicators):
                return CitationType.ARTICLE_JOURNAL
            # Check for newspaper indicators
            newspaper_indicators = ['times', 'post', 'herald', 'news', 'daily', 'weekly']
            if any(indicator in container_str for indicator in newspaper_indicators):
                return CitationType.ARTICLE_NEWSPAPER
            # Default container titles to journal articles
            return CitationType.ARTICLE_JOURNAL
        
        # Check for books
        if self.publisher or self.location:
            # Look for academic press indicators
            press_indicators = ['university press', 'academic press', 'press', 'publisher', 'publishing']
            if any(indicator in publisher_str for indicator in press_indicators):
                return CitationType.BOOK
            return CitationType.BOOK
        
        # Check for volume/issue numbers (likely journal articles)
        if self.volume or self.issue:
            return CitationType.ARTICLE_JOURNAL
        
        # Check for thesis indicators in title
        thesis_indicators = ['dissertation', 'thesis', 'phd', 'master\'s', 'doctoral']
        if any(indicator in title_str for indicator in thesis_indicators):
            return CitationType.THESIS
        
        # Check for report indicators
        report_indicators = ['report', 'working paper', 'technical report', 'policy brief']
        if any(indicator in title_str for indicator in report_indicators):
            return CitationType.REPORT
        
        # Check for chapter indicators
        if 'chapter' in title_str or 'in:' in title_str:
            return CitationType.CHAPTER
        
        # Check for webpage indicators  
        if any(indicator in title_str for indicator in ['website', 'blog', 'online', 'web']):
            return CitationType.WEBPAGE
        
        # Default fallback
        return CitationType.OTHER
    
    def has_valid_content(self) -> bool:
        """Check if citation has enough content to be useful."""
        # Must have a title
        if not self.title:
            return False
            
        title_str = str(self.title).lower()
        
        # Check minimum title length
        if len(str(self.title)) < 10:
            return False
            
        # Filter out common junk patterns identified in TODO analysis
        junk_patterns = [
            "ibid",
            "this content downloaded from",
            "all use subject to jstor",
            "terms and conditions of use",
            "access provided by",
            "downloaded by",
            "jstor is a not-for-profit",
            "the main topic discussed in",
            "790–791",  # Page number fragments
        ]
        
        for pattern in junk_patterns:
            if pattern in title_str:
                return False
        
        # Filter out entries that are just IP addresses or URLs
        if any(char.isdigit() for char in title_str) and ("." in title_str):
            # Check if it looks like an IP address pattern
            import re
            if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', title_str):
                return False
        
        # Filter out entries that are mostly punctuation or numbers
        alphanumeric_chars = sum(1 for c in title_str if c.isalnum())
        if alphanumeric_chars < len(title_str) * 0.6:  # Less than 60% alphanumeric
            return False
        
        # Filter out entries that appear to be sentence fragments or incomplete
        if title_str.endswith(("the", "in", "of", "and", "or", "but", "was", "were")):
            return False
            
        # Must have either author or editor for a valid citation
        if not self.author and not self.editor:
            return False
            
        return True


class BibliographyConfig(BaseModel):
    """Configuration for bibliography generation."""
    style: str = Field(default="chicago", description="Citation style")
    output_format: str = Field(default="divided", description="Output format type")
    output_file: Optional[str] = Field(None, description="Output filename")
    
    @validator('style')
    def validate_style(cls, v):
        """Validate citation style."""
        allowed_styles = ["chicago", "apa", "harvard"]
        if v.lower() not in allowed_styles:
            raise ValueError(f"Style must be one of: {allowed_styles}")
        return v.lower()
    
    @validator('output_format')
    def validate_output_format(cls, v):
        """Validate output format."""
        allowed_formats = ["divided", "combined", "sources"]
        if v.lower() not in allowed_formats:
            raise ValueError(f"Output format must be one of: {allowed_formats}")
        return v.lower()


class ProcessingResult(BaseModel):
    """Result of processing citations."""
    total_citations: int = Field(description="Total number of citations processed")
    valid_citations: int = Field(description="Number of valid citations")
    output_files: List[str] = Field(default_factory=list, description="Generated output files")
    errors: List[str] = Field(default_factory=list, description="Processing errors")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of citation processing."""
        if self.total_citations == 0:
            return 0.0
        return self.valid_citations / self.total_citations