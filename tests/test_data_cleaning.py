"""Tests for data cleaning and normalization improvements."""

import pytest
from pdfsources.formatters.base import clean_extracted_text, normalize_author_case
from pdfsources.writers import parse_citation, get_citation_signature
from pdfsources.models import CitationType


class TestDataCleaning:
    """Tests for data cleaning functions."""
    
    def test_clean_extracted_text_removes_backslashes(self):
        """Test removal of double backslashes from PDF extraction."""
        dirty_text = "This is a title with \\\\double backslashes\\\\."
        cleaned = clean_extracted_text(dirty_text)
        assert "\\\\" not in cleaned
        assert cleaned == "This is a title with double backslashes."
    
    def test_clean_extracted_text_fixes_escaped_chars(self):
        """Test fixing of escaped characters from anystyle."""
        dirty_text = "Title with \\(parentheses\\) and \\\"quotes\\\"."
        cleaned = clean_extracted_text(dirty_text)
        assert cleaned == 'Title with (parentheses) and "quotes".'
    
    def test_clean_extracted_text_fixes_escaped_brackets(self):
        """Test fixing of escaped brackets from anystyle."""
        dirty_text = "Title with \\[brackets\\] and data."
        cleaned = clean_extracted_text(dirty_text)
        assert cleaned == "Title with [brackets] and data."
    
    def test_clean_extracted_text_removes_html_entities(self):
        """Test removal of HTML entities."""
        dirty_text = "Title with &lt;brackets&gt; and &amp; symbols."
        cleaned = clean_extracted_text(dirty_text)
        assert cleaned == "Title with <brackets> and & symbols."
    
    def test_clean_extracted_text_normalizes_whitespace(self):
        """Test normalization of excessive whitespace."""
        dirty_text = "Title   with    excessive\n\n   whitespace."
        cleaned = clean_extracted_text(dirty_text)
        assert cleaned == "Title with excessive whitespace."


class TestAuthorNormalization:
    """Tests for author name normalization."""
    
    def test_normalize_author_case_handles_all_caps(self):
        """Test conversion of ALL CAPS names to Title Case."""
        caps_name = "SMITH, JOHN"
        normalized = normalize_author_case(caps_name)
        assert normalized == "Smith, John"
    
    def test_normalize_author_case_preserves_particles(self):
        """Test preservation of lowercase particles."""
        name_with_particle = "Van Der Berg, Johannes"
        normalized = normalize_author_case(name_with_particle)
        assert "van" in normalized
        assert "der" in normalized  # "der" is also a valid German particle
        assert normalized == "van der Berg, Johannes"
    
    def test_normalize_author_case_handles_irish_names(self):
        """Test handling of Irish/Scottish name prefixes."""
        irish_name = "O'Connor, Patrick"
        normalized = normalize_author_case(irish_name)
        assert normalized == "O'Connor, Patrick"
        
        scottish_name = "McDonald, Alan"
        normalized = normalize_author_case(scottish_name)
        assert normalized == "McDonald, Alan"


class TestEnhancedFiltering:
    """Tests for enhanced citation filtering."""
    
    @pytest.mark.parametrize("junk_title", [
        "This content downloaded from 92.237.237.50 on Tue, 01 Feb 2022",
        "All use subject to JSTOR Terms and Conditions",
        "Access provided by University Library",
        "JSTOR is a not-for-profit service",
        "The main topic discussed in the Legislative Bureau",
        "790–791",
    ])
    def test_has_valid_content_filters_junk(self, junk_title):
        """Test filtering of junk entries identified in TODO analysis."""
        citation_data = {
            "title": [junk_title],
            "author": [{"family": "Test", "given": "Author"}],
            "date": ["2024"]
        }
        citation = parse_citation(citation_data)
        assert not citation.has_valid_content()
    
    def test_has_valid_content_filters_ip_addresses(self):
        """Test filtering of IP addresses."""
        citation_data = {
            "title": ["Content from 192.168.1.1 server access"],
            "author": [{"family": "Test", "given": "Author"}],
            "date": ["2024"]
        }
        citation = parse_citation(citation_data)
        assert not citation.has_valid_content()
    
    def test_has_valid_content_filters_incomplete_sentences(self):
        """Test filtering of sentence fragments."""
        citation_data = {
            "title": ["This title ends with incomplete word the"],
            "author": [{"family": "Test", "given": "Author"}],
            "date": ["2024"]
        }
        citation = parse_citation(citation_data)
        assert not citation.has_valid_content()
    
    def test_has_valid_content_requires_author_or_editor(self):
        """Test requirement for author or editor."""
        citation_data = {
            "title": ["Valid Title That Is Long Enough"],
            "date": ["2024"]
        }
        citation = parse_citation(citation_data)
        assert not citation.has_valid_content()
    
    def test_has_valid_content_accepts_valid_citations(self):
        """Test acceptance of valid citations."""
        citation_data = {
            "title": ["Valid Academic Title That Is Long Enough"],
            "author": [{"family": "Smith", "given": "John"}],
            "date": ["2024"],
            "publisher": ["Academic Press"]
        }
        citation = parse_citation(citation_data)
        assert citation.has_valid_content()


class TestEnhancedTyping:
    """Tests for enhanced citation type inference."""
    
    def test_inferred_type_recognizes_journals(self):
        """Test recognition of journal articles."""
        citation_data = {
            "title": ["Test Article Title That Is Long Enough"],
            "author": [{"family": "Smith", "given": "John"}],
            "container-title": ["Journal of Testing"]
        }
        citation = parse_citation(citation_data)
        assert citation.get_inferred_type() == CitationType.ARTICLE_JOURNAL
    
    def test_inferred_type_recognizes_newspapers(self):
        """Test recognition of newspaper articles."""
        citation_data = {
            "title": ["Breaking News Article Title That Is Long Enough"],
            "author": [{"family": "Reporter", "given": "Jane"}],
            "container-title": ["The Daily Times"]
        }
        citation = parse_citation(citation_data)
        assert citation.get_inferred_type() == CitationType.ARTICLE_NEWSPAPER
    
    def test_inferred_type_recognizes_books_by_publisher(self):
        """Test recognition of books by publisher."""
        citation_data = {
            "title": ["Academic Book Title That Is Long Enough"],
            "author": [{"family": "Author", "given": "Academic"}],
            "publisher": ["University Press"]
        }
        citation = parse_citation(citation_data)
        assert citation.get_inferred_type() == CitationType.BOOK
    
    def test_inferred_type_recognizes_thesis(self):
        """Test recognition of thesis/dissertation."""
        citation_data = {
            "title": ["PhD Dissertation on Important Topic That Is Long Enough"],
            "author": [{"family": "Student", "given": "Graduate"}]
        }
        citation = parse_citation(citation_data)
        assert citation.get_inferred_type() == CitationType.THESIS
    
    def test_inferred_type_recognizes_reports(self):
        """Test recognition of reports."""
        citation_data = {
            "title": ["Technical Report on Software Engineering That Is Long Enough"],
            "author": [{"family": "Engineer", "given": "Software"}]
        }
        citation = parse_citation(citation_data)
        assert citation.get_inferred_type() == CitationType.REPORT


class TestDeduplication:
    """Tests for citation deduplication."""
    
    def test_citation_signature_generation(self):
        """Test generation of citation signatures."""
        citation_data = {
            "title": ["Test Article Title That Is Long Enough"],
            "author": [{"family": "Smith", "given": "John"}],
            "date": ["2024"]
        }
        citation = parse_citation(citation_data)
        signature = get_citation_signature(citation)
        
        assert isinstance(signature, str)
        assert len(signature) > 0
        assert "testarticletitle" in signature  # Title part
        assert "smith" in signature  # Author part
        assert "2024" in signature  # Year part
    
    def test_citation_signature_consistency(self):
        """Test that identical citations produce identical signatures."""
        citation_data = {
            "title": ["Test Article Title That Is Long Enough"],
            "author": [{"family": "Smith", "given": "John"}],
            "date": ["2024"]
        }
        
        citation1 = parse_citation(citation_data)
        citation2 = parse_citation(citation_data)
        
        signature1 = get_citation_signature(citation1)
        signature2 = get_citation_signature(citation2)
        
        assert signature1 == signature2
    
    def test_citation_signature_differs_for_different_citations(self):
        """Test that different citations produce different signatures."""
        citation1_data = {
            "title": ["First Article Title That Is Long Enough"],
            "author": [{"family": "Smith", "given": "John"}],
            "date": ["2024"]
        }
        
        citation2_data = {
            "title": ["Second Article Title That Is Long Enough"],
            "author": [{"family": "Jones", "given": "Jane"}],
            "date": ["2023"]
        }
        
        citation1 = parse_citation(citation1_data)
        citation2 = parse_citation(citation2_data)
        
        signature1 = get_citation_signature(citation1)
        signature2 = get_citation_signature(citation2)
        
        assert signature1 != signature2