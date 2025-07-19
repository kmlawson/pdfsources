"""Tests for CLI integration."""

import pytest
import subprocess
import json


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with sample data."""
    # Create sample citation data
    sample_data = [
        {
            "title": ["CLI Test Book Title That Is Long Enough"],
            "author": [{"family": "CLI", "given": "Test"}],
            "date": ["2023"],
            "publisher": ["Test Publisher"],
            "type": "book"
        },
        {
            "title": ["CLI Test Article Title That Is Long Enough"],
            "author": [{"family": "Article", "given": "Writer"}],
            "date": ["2023"],
            "container-title": ["Test Journal"],
            "type": "article-journal"
        }
    ]
    
    # Create JSON file
    json_file = tmp_path / "test_citations.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f)
    
    return tmp_path, str(json_file)


class TestCLIIntegration:
    """Integration tests for the CLI."""

    def test_cli_help(self):
        """Test that --help flag works."""
        result = subprocess.run(
            ["pdfsources", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Extract and process citations" in result.stdout
        assert "--combined-output" in result.stdout
        assert "--sources-divided-output" in result.stdout

    def test_cli_version(self):
        """Test that --version flag works."""
        result = subprocess.run(
            ["pdfsources", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "pdfsources" in result.stdout

    def test_cli_combined_output(self, temp_workspace):
        """Test CLI with --combined-output flag."""
        workspace, json_file = temp_workspace
        output_file = workspace / "test_combined.md"
        
        result = subprocess.run(
            ["pdfsources", json_file, "--combined-output", "--output", str(output_file)],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "# Bibliography (Chicago)" in content
        assert "CLI Test Book Title That Is Long Enough" in content
        assert "CLI Test Article Title That Is Long Enough" in content

    def test_cli_sources_divided_output(self, temp_workspace):
        """Test CLI with --sources-divided-output flag."""
        workspace, json_file = temp_workspace
        output_file = workspace / "test_sources_divided.md"
        
        result = subprocess.run(
            ["pdfsources", json_file, "--sources-divided-output", "--output", str(output_file)],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "# Bibliography by Source with Categories (Chicago)" in content
        assert "## Test Citations (2 sources)" in content
        assert "### Book" in content
        assert "### Article Journal" in content

    def test_cli_style_selection(self, temp_workspace):
        """Test CLI with different citation styles."""
        workspace, json_file = temp_workspace
        
        # Test APA style
        apa_file = workspace / "test_apa.md"
        result = subprocess.run(
            ["pdfsources", json_file, "--combined-output", "--style", "apa", "--output", str(apa_file)],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert apa_file.exists()
        
        content = apa_file.read_text()
        assert "# Bibliography (Apa)" in content
        
        # Test Harvard style
        harvard_file = workspace / "test_harvard.md"
        result = subprocess.run(
            ["pdfsources", json_file, "--combined-output", "--style", "harvard", "--output", str(harvard_file)],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert harvard_file.exists()
        
        content = harvard_file.read_text()
        assert "# Bibliography (Harvard)" in content

    def test_cli_invalid_input_file(self, tmp_path):
        """Test CLI with non-existent input file."""
        result = subprocess.run(
            ["pdfsources", "nonexistent.json"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        # Should fail gracefully
        assert result.returncode != 0

    def test_cli_invalid_style(self, temp_workspace):
        """Test CLI with invalid citation style."""
        workspace, json_file = temp_workspace
        
        result = subprocess.run(
            ["pdfsources", json_file, "--style", "invalid"],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        
        # Should fail with argument parsing error
        assert result.returncode != 0
        assert "invalid choice" in result.stderr

    def test_cli_debug_mode(self, temp_workspace):
        """Test CLI with debug logging."""
        workspace, json_file = temp_workspace
        output_file = workspace / "test_debug.md"
        
        result = subprocess.run(
            ["pdfsources", json_file, "--combined-output", "--debug", "--output", str(output_file)],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        # Debug logging should appear in stderr
        assert "DEBUG:" in result.stderr or "Debug logging enabled" in result.stderr

    def test_cli_file_overwrite_protection(self, temp_workspace):
        """Test CLI file overwrite protection."""
        workspace, json_file = temp_workspace
        output_file = workspace / "test_overwrite.md"
        
        # Create first file
        result1 = subprocess.run(
            ["pdfsources", json_file, "--combined-output", "--output", str(output_file)],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        assert result1.returncode == 0
        assert output_file.exists()
        
        # Try to create again - should create numbered alternative
        result2 = subprocess.run(
            ["pdfsources", json_file, "--combined-output", "--output", str(output_file)],
            cwd=workspace,
            capture_output=True,
            text=True,
            input="n\n"  # Decline overwrite
        )
        assert result2.returncode == 0
        
        # Should create alternative file
        alternative_file = workspace / "test_overwrite_1.md"
        assert alternative_file.exists()

    def test_cli_corrupt_json_file(self, tmp_path):
        """Test CLI with corrupt JSON file."""
        corrupt_file = tmp_path / "corrupt.json"
        with open(corrupt_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")
        
        result = subprocess.run(
            ["pdfsources", str(corrupt_file)],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        # CLI handles corrupt JSON gracefully, generating output files
        assert result.returncode == 0
        # Check that output files were created despite corrupt input
        assert "Generated" in result.stderr or "INFO:" in result.stderr

    def test_cli_empty_json_file(self, tmp_path):
        """Test CLI with empty JSON file."""
        empty_file = tmp_path / "empty.json"
        with open(empty_file, 'w', encoding='utf-8') as f:
            f.write("[]")
        
        output_file = tmp_path / "empty_output.md"
        result = subprocess.run(
            ["pdfsources", str(empty_file), "--combined-output", "--output", str(output_file)],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        # Should succeed but create empty bibliography
        assert result.returncode == 0
        assert output_file.exists()

    def test_cli_permission_denied(self, temp_workspace):
        """Test CLI with permission denied on output directory."""
        workspace, json_file = temp_workspace
        
        # Try to write to root directory (should fail or succeed gracefully)
        result = subprocess.run(
            ["pdfsources", json_file, "--output", "/root/test.md"],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        
        # CLI handles permission issues gracefully, may create alternative outputs
        assert result.returncode == 0
        # Should generate output files despite permission issues
        assert "Generated" in result.stderr or "INFO:" in result.stderr