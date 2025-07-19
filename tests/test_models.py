"""Tests for pydantic models."""

import pytest
from pydantic import ValidationError

from pdfsources.models import Citation, Person, BibliographyConfig, ProcessingResult, CitationType


class TestPerson:
    """Tests for Person model."""
    
    def test_valid_person(self):
        """Test creating a valid person."""
        person = Person(family="Smith", given="John")
        assert person.family == "Smith"
        assert person.given == "John"
    
    def test_person_with_whitespace(self):
        """Test that whitespace is cleaned from names."""
        person = Person(family="  Smith  ", given="  John  ")
        assert person.family == "Smith"
        assert person.given == "John"
    
    def test_partial_person(self):
        """Test creating person with only family name."""
        person = Person(family="Smith")
        assert person.family == "Smith"
        assert person.given is None


class TestCitation:
    """Tests for Citation model."""
    
    def test_valid_citation(self):
        """Test creating a valid citation."""
        citation_data = {
            "title": "Test Title",
            "author": [{"family": "Smith", "given": "John"}],
            "date": "2023",
            "publisher": "Test Publisher"
        }
        citation = Citation(**citation_data)
        assert citation.title == "Test Title"
        assert len(citation.author) == 1
        assert citation.author[0].family == "Smith"
    
    def test_citation_with_list_fields(self):
        """Test citation with fields that come as lists."""
        citation_data = {
            "title": ["Test Title"],
            "date": ["2023"],
            "volume": ["10"]
        }
        citation = Citation(**citation_data)
        assert citation.title == "Test Title"
        assert citation.date == "2023"
        assert citation.volume == "10"
    
    def test_citation_type_inference(self):
        """Test citation type inference."""
        # Book citation
        book_citation = Citation(
            title="Test Book",
            publisher="Test Publisher"
        )
        assert book_citation.get_inferred_type() == CitationType.BOOK
        
        # Journal article citation
        article_citation = Citation(
            title="Test Article",
            container_title="Test Journal"
        )
        assert article_citation.get_inferred_type() == CitationType.ARTICLE_JOURNAL
        
        # Generic citation
        generic_citation = Citation(title="Test")
        assert generic_citation.get_inferred_type() == CitationType.GENERIC
    
    def test_citation_validity(self):
        """Test citation validity checking."""
        # Valid citation
        valid_citation = Citation(title="This is a valid title with enough content")
        assert valid_citation.has_valid_content() is True
        
        # Invalid citations
        no_title_citation = Citation()
        assert no_title_citation.has_valid_content() is False
        
        short_title_citation = Citation(title="Short")
        assert short_title_citation.has_valid_content() is False
        
        ibid_citation = Citation(title="ibid.")
        assert ibid_citation.has_valid_content() is False
    
    def test_citation_with_extra_fields(self):
        """Test that extra fields are allowed."""
        citation_data = {
            "title": "Test Title",
            "custom_field": "custom_value",
            "another_field": 123
        }
        citation = Citation(**citation_data)
        assert citation.title == "Test Title"
        # Extra fields should be accessible
        assert hasattr(citation, 'custom_field')


class TestBibliographyConfig:
    """Tests for BibliographyConfig model."""
    
    def test_valid_config(self):
        """Test creating valid configuration."""
        config = BibliographyConfig(
            style="chicago",
            output_format="divided",
            output_file="test.md"
        )
        assert config.style == "chicago"
        assert config.output_format == "divided"
        assert config.output_file == "test.md"
    
    def test_default_config(self):
        """Test default configuration values."""
        config = BibliographyConfig()
        assert config.style == "chicago"
        assert config.output_format == "divided"
        assert config.output_file is None
    
    def test_invalid_style(self):
        """Test validation of invalid style."""
        with pytest.raises(ValidationError):
            BibliographyConfig(style="invalid_style")
    
    def test_invalid_output_format(self):
        """Test validation of invalid output format."""
        with pytest.raises(ValidationError):
            BibliographyConfig(output_format="invalid_format")
    
    def test_case_insensitive_validation(self):
        """Test case insensitive validation."""
        config = BibliographyConfig(style="CHICAGO", output_format="DIVIDED")
        assert config.style == "chicago"
        assert config.output_format == "divided"


class TestProcessingResult:
    """Tests for ProcessingResult model."""
    
    def test_processing_result(self):
        """Test creating processing result."""
        result = ProcessingResult(
            total_citations=100,
            valid_citations=95,
            output_files=["test1.md", "test2.md"],
            errors=["Error 1"]
        )
        assert result.total_citations == 100
        assert result.valid_citations == 95
        assert len(result.output_files) == 2
        assert len(result.errors) == 1
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = ProcessingResult(total_citations=100, valid_citations=95)
        assert result.success_rate == 0.95
        
        # Test with zero citations
        zero_result = ProcessingResult(total_citations=0, valid_citations=0)
        assert zero_result.success_rate == 0.0
    
    def test_default_processing_result(self):
        """Test default processing result values."""
        result = ProcessingResult(total_citations=10, valid_citations=8)
        assert result.output_files == []
        assert result.errors == []