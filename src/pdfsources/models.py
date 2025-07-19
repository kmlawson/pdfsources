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
    GENERIC = "generic"


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
        """Infer citation type based on available fields."""
        if self.type:
            # Try to match known types
            type_str = self.type.lower() if isinstance(self.type, str) else str(self.type).lower()
            for ct in CitationType:
                if ct.value in type_str:
                    return ct
        
        # Fallback inference logic
        if self.container_title:
            return CitationType.ARTICLE_JOURNAL
        elif self.publisher or self.location:
            return CitationType.BOOK
        else:
            return CitationType.GENERIC
    
    def has_valid_content(self) -> bool:
        """Check if citation has enough content to be useful."""
        # Must have a title
        if not self.title:
            return False
            
        # Check for common invalid patterns
        title_str = str(self.title).lower()
        if "ibid" in title_str or len(str(self.title)) < 10:
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