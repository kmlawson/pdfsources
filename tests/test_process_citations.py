import pytest
import json
from pdfsources.formatters import ChicagoFormatter, APAFormatter, HarvardFormatter
from pdfsources.writers import BibliographyWriter, parse_citation
from test_helpers import (validate_citation_fields, validate_bibliography_structure, validate_divided_bibliography,
                          validate_sources_bibliography)


@pytest.fixture
def sample_citations():
    """Sample citation data for testing."""
    return [
        {
            "title": ["Test Book Title That Is Long Enough"],
            "author": [{"family": "Author", "given": "A."}],
            "date": ["2025"],
            "location": ["Test City"],
            "publisher": ["Test Publisher"],
            "type": "book"
        },
        {
            "title": ["Test Article Title That Is Long Enough"],
            "author": [{"family": "Writer", "given": "B."}],
            "date": ["2024"],
            "container-title": ["Test Journal"],
            "type": "article-journal"
        },
        {
            "title": ["Another Article Title That Is Long Enough"],
            "author": [{"family": "Editor", "given": "C."}],
            "date": ["2023"],
            "container-title": ["Another Journal"],
            "type": "article-journal"
        }
    ]


@pytest.fixture
def temp_json_files(sample_citations, tmp_path):
    """Create temporary JSON files with citation data."""
    json_file_1 = tmp_path / "test_citations.json"
    json_file_2 = tmp_path / "test_citations_2.json"
    
    with open(json_file_1, 'w', encoding='utf-8') as f:
        json.dump(sample_citations, f)
    
    with open(json_file_2, 'w', encoding='utf-8') as f:
        json.dump([sample_citations[0]], f)
    
    return str(json_file_1), str(json_file_2)


class TestCitationFormatters:
    """Tests for citation formatting functions."""

    @pytest.mark.parametrize("formatter,style_name", [
        (ChicagoFormatter(), "chicago"),
        (APAFormatter(), "apa"),
        (HarvardFormatter(), "harvard")
    ])
    def test_formatters_basic(self, sample_citations, formatter, style_name):
        """Test basic formatting for all citation styles using semantic validation."""
        book_citation = parse_citation(sample_citations[0])
        article_citation = parse_citation(sample_citations[1])
        
        book_result = formatter.format(book_citation)
        article_result = formatter.format(article_citation)
        
        # Use semantic validation instead of exact string matching
        book_validation = validate_citation_fields(book_result, ["author", "title", "year", "publisher"])
        article_validation = validate_citation_fields(article_result, ["author", "title", "year"])
        
        # Verify essential components are present
        assert book_validation["author"], f"Book citation missing author: {book_result}"
        assert book_validation["title"], f"Book citation missing title: {book_result}"
        assert book_validation["year"], f"Book citation missing year: {book_result}"
        
        assert article_validation["author"], f"Article citation missing author: {article_result}"
        assert article_validation["title"], f"Article citation missing title: {article_result}"
        assert article_validation["year"], f"Article citation missing year: {article_result}"
        
        # Verify non-empty results
        assert book_result.strip(), "Book citation should not be empty"
        assert article_result.strip(), "Article citation should not be empty"

    def test_multiple_authors(self):
        """Test formatting with multiple authors."""
        citation_data = {
            "title": ["Multi-Author Book Title That Is Long Enough"],
            "author": [
                {"family": "Smith", "given": "John"},
                {"family": "Jones", "given": "Jane"},
                {"family": "Johnson", "given": "Jack"}
            ],
            "date": ["2023"],
            "publisher": ["Test Publisher"],
            "type": "book"
        }
        citation = parse_citation(citation_data)
        
        chicago_result = ChicagoFormatter().format(citation)
        assert "Smith, John, Jones, Jane, and Johnson, Jack" in chicago_result
        
        apa_result = APAFormatter().format(citation)
        assert "Smith, John, Jones, Jane, and Johnson, Jack" in apa_result

    def test_missing_fields(self):
        """Test formatting with missing fields."""
        minimal_citation = {
            "title": ["Minimal Citation Title That Is Long Enough"],
            "author": [{"family": "Author", "given": "A."}],
            "type": "generic"
        }
        citation = parse_citation(minimal_citation)
        
        # Should still produce output despite missing fields
        chicago_result = ChicagoFormatter().format(citation)
        assert "Minimal Citation Title That Is Long Enough" in chicago_result
        assert chicago_result != ""
        
        apa_result = APAFormatter().format(citation)
        assert "Minimal Citation Title That Is Long Enough" in apa_result
        assert apa_result != ""

    def test_no_author(self):
        """Test that citations without authors are filtered out."""
        no_author_citation = {
            "title": ["Anonymous Work Title That Is Long Enough"],
            "date": ["2023"],
            "publisher": ["Test Publisher"],
            "type": "book"
        }
        citation = parse_citation(no_author_citation)
        
        # Should now be invalid due to enhanced filtering
        assert not citation.has_valid_content()
        
        chicago_result = ChicagoFormatter().format(citation)
        assert chicago_result == ""  # Empty because invalid
        
    def test_editors_instead_of_authors(self):
        """Test formatting with editors instead of authors."""
        editor_citation = {
            "title": ["Edited Volume Title That Is Long Enough"],
            "editor": [{"family": "Editor", "given": "E."}],
            "date": ["2023"],
            "publisher": ["Test Publisher"],
            "type": "book"
        }
        citation = parse_citation(editor_citation)
        
        chicago_result = ChicagoFormatter().format(citation)
        assert "Editor, E., eds." in chicago_result

    def test_invalid_citation(self):
        """Test formatting with invalid citation data."""
        invalid_citation = {
            "title": ["Short"],  # Too short title
            "author": [{"family": "Author", "given": "A."}]
        }
        citation = parse_citation(invalid_citation)
        
        # Should return empty string for invalid citations
        assert ChicagoFormatter().format(citation) == ""
        assert APAFormatter().format(citation) == ""
        assert HarvardFormatter().format(citation) == ""


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_corrupt_json_file(self, tmp_path):
        """Test handling of corrupt JSON files."""
        corrupt_file = tmp_path / "corrupt.json"
        with open(corrupt_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")
        
        # Should handle JSON errors gracefully
        writer = BibliographyWriter(ChicagoFormatter())
        output_file = tmp_path / "output.md"
        
        # The writer should handle corrupt JSON gracefully, not crash
        writer.write_combined_bibliography(str(output_file), [str(corrupt_file)])
        
        # Verify output file was created and has proper structure
        assert output_file.exists(), "Output file should be created even with corrupt input"
        content = output_file.read_text()
        assert "# Bibliography" in content, "Should have bibliography header even with no valid citations"

    def test_empty_json_file(self, tmp_path):
        """Test handling of empty JSON files."""
        empty_file = tmp_path / "empty.json"
        with open(empty_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
        
        output_file = tmp_path / "output.md"
        writer = BibliographyWriter(ChicagoFormatter())
        writer.write_combined_bibliography(str(output_file), [str(empty_file)])
        
        # Should create output file even with no citations
        assert output_file.exists()
        content = output_file.read_text()
        assert "# Bibliography" in content

    def test_nonexistent_file(self, tmp_path):
        """Test handling of non-existent input files."""
        nonexistent_file = str(tmp_path / "does_not_exist.json")
        output_file = tmp_path / "output.md"
        
        # Should handle missing files gracefully
        writer = BibliographyWriter(ChicagoFormatter())
        
        # The writer should handle missing files gracefully, not crash
        writer.write_combined_bibliography(str(output_file), [nonexistent_file])
        
        # Verify output file was created and has proper structure
        assert output_file.exists(), "Output file should be created even with missing input files"
        content = output_file.read_text()
        assert "# Bibliography" in content, "Should have bibliography header even with no valid input files"

    def test_invalid_output_directory(self, temp_json_files):
        """Test handling of invalid output directory."""
        json_file_1, _ = temp_json_files
        invalid_output = "/nonexistent/directory/output.md"
        
        # Should raise appropriate error for invalid output path
        writer = BibliographyWriter(ChicagoFormatter())
        
        # This should actually fail with a proper exception
        with pytest.raises((FileNotFoundError, PermissionError, OSError)) as exc_info:
            writer.write_combined_bibliography(invalid_output, [json_file_1])
        
        # Verify we get a meaningful error message
        assert str(exc_info.value), "Should provide a meaningful error message"

    def test_malformed_citation_data(self, tmp_path):
        """Test handling of malformed citation data."""
        malformed_data = [
            {"invalid": "data"},
            {"title": None},
            {"title": []},
            {"title": [""], "author": "not a list"},
        ]
        
        malformed_file = tmp_path / "malformed.json"
        with open(malformed_file, 'w', encoding='utf-8') as f:
            json.dump(malformed_data, f)
        
        output_file = tmp_path / "output.md"
        writer = BibliographyWriter(ChicagoFormatter())
        writer.write_combined_bibliography(str(output_file), [str(malformed_file)])
        
        # Should create output file and filter out invalid citations
        assert output_file.exists()
        content = output_file.read_text()
        assert "# Bibliography" in content


class TestBibliographyWriter:
    """Tests for the BibliographyWriter class."""

    def test_write_divided_bibliography(self, temp_json_files, tmp_path):
        """Test the write_divided_bibliography method."""
        json_file_1, json_file_2 = temp_json_files
        output_file = tmp_path / "bibliography_divided.md"
        
        writer = BibliographyWriter(ChicagoFormatter())
        writer.write_divided_bibliography(str(output_file), [json_file_1])
        assert output_file.exists()
        
        content = output_file.read_text()
        
        # Use semantic validation instead of exact string matching
        structure_validation = validate_bibliography_structure(content, "chicago")
        divided_validation = validate_divided_bibliography(content)
        
        assert structure_validation["has_header"], "Bibliography should have main header"
        assert structure_validation["has_correct_style"], "Bibliography should specify Chicago style"
        assert structure_validation["has_citations"], "Bibliography should contain citations"
        
        assert divided_validation["has_sections"], "Divided bibliography should have sections"
        assert divided_validation["has_book_section"], "Should have book section"
        assert divided_validation["has_article_section"], "Should have article section"

    def test_write_combined_bibliography(self, temp_json_files, tmp_path):
        """Test the write_combined_bibliography method."""
        json_file_1, json_file_2 = temp_json_files
        output_file = tmp_path / "bibliography_combined.md"
        
        writer = BibliographyWriter(ChicagoFormatter())
        writer.write_combined_bibliography(str(output_file), [json_file_1])
        assert output_file.exists()
        
        content = output_file.read_text()
        
        # Use semantic validation
        structure_validation = validate_bibliography_structure(content, "chicago")
        
        assert structure_validation["has_header"], "Bibliography should have main header"
        assert structure_validation["has_correct_style"], "Bibliography should specify Chicago style"
        assert structure_validation["has_citations"], "Bibliography should contain citations"
        assert structure_validation["proper_formatting"], "Citations should have proper author formatting"

    def test_write_sources_bibliography(self, temp_json_files, tmp_path):
        """Test the write_sources_bibliography method."""
        json_file_1, json_file_2 = temp_json_files
        output_file = tmp_path / "bibliography_sources.md"
        
        writer = BibliographyWriter(ChicagoFormatter())
        writer.write_sources_bibliography(str(output_file), [json_file_1, json_file_2])
        assert output_file.exists()
        
        content = output_file.read_text()
        
        # Use semantic validation
        sources_validation = validate_sources_bibliography(content, ["test_citations", "test_citations_2"])
        
        assert sources_validation["has_source_sections"], "Should have source sections"
        assert sources_validation["source_sections_have_counts"], "Source sections should have citation counts"
        
        # Check for sources header
        assert "# Bibliography by Source (Chicago)" in content, "Should have sources bibliography header"

    def test_write_sources_divided_bibliography(self, temp_json_files, tmp_path):
        """Test the write_sources_divided_bibliography method."""
        json_file_1, json_file_2 = temp_json_files
        output_file = tmp_path / "bibliography_sources_divided.md"
        
        writer = BibliographyWriter(ChicagoFormatter())
        writer.write_sources_divided_bibliography(str(output_file), [json_file_1])
        assert output_file.exists()
        
        content = output_file.read_text()
        
        # Use semantic validation
        sources_validation = validate_sources_bibliography(content)
        divided_validation = validate_divided_bibliography(content)
        
        assert sources_validation["has_source_sections"], "Should have source sections"
        assert divided_validation["has_sections"], "Should have category sections"
        
        # Check for specific headers
        assert "# Bibliography by Source with Categories (Chicago)" in content, "Should have correct header"
        assert "### Book" in content or "### Article" in content, "Should have subsection categories"