import pytest
import json
from pdfsources.formatters import ChicagoFormatter, APAFormatter, HarvardFormatter
from pdfsources.writers import BibliographyWriter, parse_citation


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

    @pytest.mark.parametrize("formatter,expected_book,expected_article", [
        (ChicagoFormatter(), 'Author, A. *Test Book Title That Is Long Enough*. (2025) Test City: Test Publisher, 2025.', 'Writer, B. "Test Article Title That Is Long Enough". (2024)'),
        (APAFormatter(), 'Author, A. (2025). Test Book Title That Is Long Enough Test City: Test Publisher.', 'Writer, B. (2024). Test Article Title That Is Long Enough'),
        (HarvardFormatter(), 'Author, A. 2025, *Test Book Title That Is Long Enough*. Test City: Test Publisher.', 'Writer, B. 2024, *Test Article Title That Is Long Enough*.')
    ])
    def test_formatters_basic(self, sample_citations, formatter, expected_book, expected_article):
        """Test basic formatting for all citation styles."""
        book_citation = parse_citation(sample_citations[0])
        article_citation = parse_citation(sample_citations[1])
        
        assert formatter.format(book_citation) == expected_book
        assert formatter.format(article_citation) == expected_article

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
        """Test formatting with no author."""
        no_author_citation = {
            "title": ["Anonymous Work Title That Is Long Enough"],
            "date": ["2023"],
            "publisher": ["Test Publisher"],
            "type": "book"
        }
        citation = parse_citation(no_author_citation)
        
        chicago_result = ChicagoFormatter().format(citation)
        assert "Anonymous Work Title That Is Long Enough" in chicago_result
        
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
        try:
            writer = BibliographyWriter(ChicagoFormatter())
            writer.write_combined_bibliography(str(tmp_path / "output.md"), [str(corrupt_file)])
        except json.JSONDecodeError:
            # Expected to raise JSONDecodeError or handle gracefully
            pass

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
        try:
            writer = BibliographyWriter(ChicagoFormatter())
            writer.write_combined_bibliography(str(output_file), [nonexistent_file])
        except (FileNotFoundError, IOError):
            # Expected to raise file error or handle gracefully
            pass

    def test_invalid_output_directory(self, temp_json_files):
        """Test handling of invalid output directory."""
        json_file_1, _ = temp_json_files
        invalid_output = "/nonexistent/directory/output.md"
        
        # Should handle invalid output path gracefully
        try:
            writer = BibliographyWriter(ChicagoFormatter())
            writer.write_combined_bibliography(invalid_output, [json_file_1])
        except (FileNotFoundError, PermissionError, OSError):
            # Expected to raise appropriate error
            pass

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
        assert "# Bibliography (Chicago)" in content
        assert "## Book" in content
        assert "## Article Journal" in content
        assert "* Author, A." in content
        assert "* Writer, B." in content

    def test_write_combined_bibliography(self, temp_json_files, tmp_path):
        """Test the write_combined_bibliography method."""
        json_file_1, json_file_2 = temp_json_files
        output_file = tmp_path / "bibliography_combined.md"
        
        writer = BibliographyWriter(ChicagoFormatter())
        writer.write_combined_bibliography(str(output_file), [json_file_1])
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "# Bibliography (Chicago)" in content
        assert "* Author, A." in content
        assert "* Writer, B." in content

    def test_write_sources_bibliography(self, temp_json_files, tmp_path):
        """Test the write_sources_bibliography method."""
        json_file_1, json_file_2 = temp_json_files
        output_file = tmp_path / "bibliography_sources.md"
        
        writer = BibliographyWriter(ChicagoFormatter())
        writer.write_sources_bibliography(str(output_file), [json_file_1, json_file_2])
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "# Bibliography by Source (Chicago)" in content
        assert "## Test Citations (3 sources)" in content
        assert "## Test Citations 2 (1 sources)" in content
        assert "* Author, A." in content
        assert "* Writer, B." in content

    def test_write_sources_divided_bibliography(self, temp_json_files, tmp_path):
        """Test the write_sources_divided_bibliography method."""
        json_file_1, json_file_2 = temp_json_files
        output_file = tmp_path / "bibliography_sources_divided.md"
        
        writer = BibliographyWriter(ChicagoFormatter())
        writer.write_sources_divided_bibliography(str(output_file), [json_file_1])
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "# Bibliography by Source with Categories (Chicago)" in content
        assert "## Test Citations (3 sources)" in content
        assert "### Book" in content
        assert "### Article Journal" in content
        assert "* Author, A." in content
        assert "* Writer, B." in content