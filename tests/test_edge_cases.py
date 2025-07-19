"""Edge case tests for pdfsources."""

import pytest
import json
from pdfsources.formatters import ChicagoFormatter, APAFormatter, HarvardFormatter
from pdfsources.writers import BibliographyWriter, parse_citation
from test_helpers import validate_citation_fields, validate_markdown_safety


class TestNonASCIICharacters:
    """Tests for non-ASCII characters, RTL scripts, and emoji in citations."""
    
    def test_unicode_author_names(self):
        """Test Unicode characters in author names."""
        citation_data = {
            "title": ["Test Article with Unicode Authors That Is Long Enough"],
            "author": [
                {"family": "García", "given": "José"},
                {"family": "Müller", "given": "François"},
                {"family": "李", "given": "明"}
            ],
            "date": ["2024"],
            "type": "article-journal"
        }
        
        citation = parse_citation(citation_data)
        formatters = [ChicagoFormatter(), APAFormatter(), HarvardFormatter()]
        
        for formatter in formatters:
            result = formatter.format(citation)
            assert result, f"{formatter.style_name} should handle Unicode authors"
            assert "García" in result, "Should preserve Spanish characters"
            assert "Müller" in result, "Should preserve German characters"
            assert "李" in result, "Should preserve Chinese characters"
            
            # Verify markdown safety
            safety = validate_markdown_safety(result)
            assert safety["no_script_tags"], "Should not introduce script tags"
    
    def test_arabic_rtl_text(self):
        """Test Right-to-Left (RTL) script handling."""
        citation_data = {
            "title": ["مقالة باللغة العربية مع عنوان طويل بما فيه الكفاية"],
            "author": [{"family": "الخوارزمي", "given": "محمد"}],
            "date": ["2024"],
            "container-title": ["مجلة علمية"],
            "type": "article-journal"
        }
        
        citation = parse_citation(citation_data)
        formatter = ChicagoFormatter()
        result = formatter.format(citation)
        
        assert result, "Should handle Arabic text"
        assert "الخوارزمي" in result, "Should preserve Arabic author name"
        assert "مقالة باللغة العربية" in result, "Should preserve Arabic title"
        
        # Verify proper escaping
        safety = validate_markdown_safety(result)
        assert safety["no_unescaped_brackets"], "Should escape special characters"
    
    def test_emoji_in_titles(self):
        """Test emoji characters in citation titles."""
        citation_data = {
            "title": ["📚 Digital Libraries and Modern Research Methods 📖"],
            "author": [{"family": "Smith", "given": "John"}],
            "date": ["2024"],
            "publisher": ["Tech Publishing"],
            "type": "book"
        }
        
        citation = parse_citation(citation_data)
        formatter = ChicagoFormatter()
        result = formatter.format(citation)
        
        assert result, "Should handle emoji in titles"
        assert "📚" in result, "Should preserve book emoji"
        assert "📖" in result, "Should preserve reading emoji"
    
    def test_mixed_scripts(self):
        """Test mixed scripts in single citation."""
        citation_data = {
            "title": ["英語と日本語 Mixed Language Article Title That Is Long Enough"],
            "author": [
                {"family": "Tanaka", "given": "田中"},
                {"family": "Smith", "given": "John"}
            ],
            "date": ["2024"],
            "container-title": ["International Journal 国際ジャーナル"],
            "type": "article-journal"
        }
        
        citation = parse_citation(citation_data)
        formatter = APAFormatter()
        result = formatter.format(citation)
        
        assert result, "Should handle mixed scripts"
        assert "田中" in result, "Should preserve Japanese characters"
        assert "英語と日本語" in result, "Should preserve Japanese text in title"
        assert "国際ジャーナル" in result, "Should preserve Japanese journal name"


class TestUnsupportedCitationTypes:
    """Tests for unsupported citation types and edge cases."""
    
    @pytest.mark.parametrize("citation_type", [
        "conference-paper",
        "thesis",
        "webpage",
        "patent",
        "software",
        "dataset",
        "unpublished",
        "manuscript"
    ])
    def test_unsupported_citation_types(self, citation_type):
        """Test handling of various unsupported citation types."""
        citation_data = {
            "title": [f"Test {citation_type.title()} Title That Is Long Enough"],
            "author": [{"family": "Author", "given": "Test"}],
            "date": ["2024"],
            "type": citation_type
        }
        
        citation = parse_citation(citation_data)
        formatters = [ChicagoFormatter(), APAFormatter(), HarvardFormatter()]
        
        for formatter in formatters:
            result = formatter.format(citation)
            # Should either format as generic or handle gracefully
            if result:  # If it formats
                validation = validate_citation_fields(result, ["author", "title"])
                assert validation["author"], f"Should preserve author for {citation_type}"
                assert validation["title"], f"Should preserve title for {citation_type}"
            # If it doesn't format, that's also acceptable for unsupported types
    
    def test_missing_required_fields(self):
        """Test citations missing critical fields."""
        test_cases = [
            {"title": ["Title Only That Is Long Enough"]},  # No author
            {"author": [{"family": "Author", "given": "Only"}]},  # No title
            {"date": ["2024"]},  # No title or author
            {}  # Empty citation
        ]
        
        for citation_data in test_cases:
            citation = parse_citation(citation_data)
            formatter = ChicagoFormatter()
            result = formatter.format(citation)
            
            # Should either handle gracefully or return empty string
            assert isinstance(result, str), "Should return string (may be empty)"
    
    def test_malformed_author_data(self):
        """Test various malformed author field formats."""
        test_cases = [
            {"author": "string instead of list"},
            {"author": [{"family": None, "given": "Test"}]},
            {"author": [{"family": "", "given": ""}]},
            {"author": [{"invalid": "field"}]},
            {"author": [123]},  # Number instead of dict
            {"author": [[]]},   # Nested list
        ]
        
        base_citation = {
            "title": ["Test Title That Is Long Enough"],
            "date": ["2024"],
            "type": "article"
        }
        
        for author_case in test_cases:
            citation_data = {**base_citation, **author_case}
            citation = parse_citation(citation_data)
            formatter = ChicagoFormatter()
            
            # Should not crash, may return empty or partial result
            result = formatter.format(citation)
            assert isinstance(result, str), f"Should handle malformed author: {author_case}"


class TestLargeDatasets:
    """Tests for performance with large datasets."""
    
    def test_large_number_of_citations(self, tmp_path):
        """Test processing large number of citations."""
        # Create dataset with 1000 citations
        large_dataset = []
        for i in range(1000):
            citation = {
                "title": [f"Test Article Number {i:04d} With Long Enough Title"],
                "author": [{"family": f"Author{i:03d}", "given": f"First{i:03d}"}],
                "date": [str(2000 + (i % 25))],  # Years 2000-2024
                "container-title": [f"Journal of Testing Volume {i % 10}"],
                "type": "article-journal"
            }
            large_dataset.append(citation)
        
        # Write to JSON file
        large_file = tmp_path / "large_dataset.json"
        with open(large_file, 'w', encoding='utf-8') as f:
            json.dump(large_dataset, f)
        
        # Test processing
        output_file = tmp_path / "large_bibliography.md"
        writer = BibliographyWriter(ChicagoFormatter())
        
        # Should complete without timeout or memory issues
        writer.write_combined_bibliography(str(output_file), [str(large_file)])
        
        assert output_file.exists(), "Should create output file for large dataset"
        content = output_file.read_text()
        
        # Verify structure
        assert "# Bibliography (Chicago)" in content, "Should have proper header"
        citation_count = content.count("* Author")
        assert citation_count == 1000, f"Should have all 1000 citations, found {citation_count}"
    
    def test_very_long_fields(self):
        """Test citations with extremely long field values."""
        long_title = "A" * 1000 + " Very Long Title That Exceeds Normal Limits"
        long_author = "B" * 500
        long_publisher = "C" * 200 + " Publishing House"
        
        citation_data = {
            "title": [long_title],
            "author": [{"family": long_author, "given": "Normal"}],
            "date": ["2024"],
            "publisher": [long_publisher],
            "location": ["Normal City"],
            "type": "book"
        }
        
        citation = parse_citation(citation_data)
        formatter = ChicagoFormatter()
        result = formatter.format(citation)
        
        assert result, "Should handle very long fields"
        # Author name will be normalized to title case (first letter capital, rest lowercase)
        normalized_author = "B" + "b" * 499  # Normalized version
        assert normalized_author in result, "Should preserve long author name (normalized)"
        assert long_title in result, "Should preserve long title"
        
        # Verify markdown safety
        safety = validate_markdown_safety(result)
        assert safety["no_script_tags"], "Should remain safe with long content"
    
    def test_deeply_nested_data(self):
        """Test handling of deeply nested or complex data structures."""
        citation_data = {
            "title": ["Standard Title That Is Long Enough"],
            "author": [
                {
                    "family": "Complex",
                    "given": "Author",
                    "extra_field": {
                        "nested": {
                            "deep": "data"
                        }
                    }
                }
            ],
            "date": ["2024"],
            "metadata": {
                "processing": {
                    "engine": "anystyle",
                    "confidence": 0.95
                }
            }
        }
        
        citation = parse_citation(citation_data)
        formatter = ChicagoFormatter()
        result = formatter.format(citation)
        
        # Should handle gracefully, ignoring unsupported nested data
        assert result, "Should handle nested data structures"
        validation = validate_citation_fields(result, ["author", "title"])
        assert validation["author"], "Should extract author despite nested data"
        assert validation["title"], "Should extract title despite nested data"


class TestSpecialCharacters:
    """Tests for special characters and markdown injection prevention."""
    
    def test_markdown_injection_prevention(self):
        """Test prevention of markdown injection attacks."""
        malicious_inputs = [
            "[Click here](http://malicious.com)",
            "![Image](javascript:alert('xss'))",
            "**Bold** and *italic* formatting",
            "```code injection```",
            "<script>alert('xss')</script>",
            "[Reference](#dangerous-link)",
            "Title with [brackets] and (parentheses)"
        ]
        
        for malicious_input in malicious_inputs:
            citation_data = {
                "title": [f"{malicious_input} - Test Title That Is Long Enough"],
                "author": [{"family": "Test", "given": malicious_input}],
                "date": ["2024"],
                "publisher": [malicious_input],
                "type": "book"
            }
            
            citation = parse_citation(citation_data)
            formatter = ChicagoFormatter()
            result = formatter.format(citation)
            
            if result:  # If citation is valid enough to format
                safety = validate_markdown_safety(result)
                assert safety["no_script_tags"], f"Should prevent script injection: {malicious_input}"
                # Note: Our escaping should handle brackets and links appropriately
    
    def test_extreme_unicode_cases(self):
        """Test extreme Unicode cases like zero-width characters."""
        special_chars = [
            "\u200B",  # Zero-width space
            "\u200C",  # Zero-width non-joiner
            "\u200D",  # Zero-width joiner
            "\uFEFF",  # Byte order mark
            "\u2028",  # Line separator
            "\u2029",  # Paragraph separator
        ]
        
        for char in special_chars:
            citation_data = {
                "title": [f"Title{char}With{char}Special{char}Characters That Is Long Enough"],
                "author": [{"family": f"Auth{char}or", "given": f"Fir{char}st"}],
                "date": ["2024"],
                "type": "article"
            }
            
            citation = parse_citation(citation_data)
            formatter = ChicagoFormatter()
            result = formatter.format(citation)
            
            # Should handle gracefully without breaking
            assert isinstance(result, str), f"Should handle special Unicode char: {repr(char)}"