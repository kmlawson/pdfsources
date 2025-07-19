"""Tests for file overwrite protection functionality."""

import os
import tempfile
from unittest.mock import patch

from pdfsources.discovery import get_safe_output_filename


class TestFileOverwriteProtection:
    """Tests for file overwrite protection."""
    
    def test_nonexistent_file(self):
        """Test that nonexistent files return unchanged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "nonexistent.md")
            result = get_safe_output_filename(test_file)
            assert result == test_file
    
    def test_user_confirms_overwrite(self):
        """Test user confirming file overwrite."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing file
            test_file = os.path.join(temp_dir, "existing.md")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("existing content")
            
            # Mock user input to confirm overwrite
            with patch('builtins.input', return_value='y'):
                result = get_safe_output_filename(test_file)
                assert result == test_file
    
    def test_user_confirms_overwrite_with_yes(self):
        """Test user confirming file overwrite with 'yes'."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing file
            test_file = os.path.join(temp_dir, "existing.md")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("existing content")
            
            # Mock user input to confirm overwrite
            with patch('builtins.input', return_value='yes'):
                result = get_safe_output_filename(test_file)
                assert result == test_file
    
    def test_user_declines_overwrite(self):
        """Test user declining file overwrite."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing file
            test_file = os.path.join(temp_dir, "existing.md")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("existing content")
            
            # Mock user input to decline overwrite
            with patch('builtins.input', return_value='n'):
                result = get_safe_output_filename(test_file)
                expected = os.path.join(temp_dir, "existing_1.md")
                assert result == expected
    
    def test_user_default_decline(self):
        """Test user pressing enter (default decline)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing file
            test_file = os.path.join(temp_dir, "existing.md")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("existing content")
            
            # Mock user input as empty (default decline)
            with patch('builtins.input', return_value=''):
                result = get_safe_output_filename(test_file)
                expected = os.path.join(temp_dir, "existing_1.md")
                assert result == expected
    
    def test_multiple_existing_files(self):
        """Test finding safe filename when multiple numbered files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple existing files
            base_file = os.path.join(temp_dir, "existing.md")
            file_1 = os.path.join(temp_dir, "existing_1.md")
            file_2 = os.path.join(temp_dir, "existing_2.md")
            
            for file_path in [base_file, file_1, file_2]:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("existing content")
            
            # Mock user input to decline overwrite
            with patch('builtins.input', return_value='n'):
                result = get_safe_output_filename(base_file)
                expected = os.path.join(temp_dir, "existing_3.md")
                assert result == expected
    
    def test_keyboard_interrupt_handling(self):
        """Test handling of KeyboardInterrupt (Ctrl+C)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing file
            test_file = os.path.join(temp_dir, "existing.md")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("existing content")
            
            # Mock user input to raise KeyboardInterrupt
            with patch('builtins.input', side_effect=KeyboardInterrupt):
                result = get_safe_output_filename(test_file)
                expected = os.path.join(temp_dir, "existing_1.md")
                assert result == expected
    
    def test_eof_error_handling(self):
        """Test handling of EOFError (non-interactive environment)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing file
            test_file = os.path.join(temp_dir, "existing.md")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("existing content")
            
            # Mock user input to raise EOFError
            with patch('builtins.input', side_effect=EOFError):
                result = get_safe_output_filename(test_file)
                expected = os.path.join(temp_dir, "existing_1.md")
                assert result == expected
    
    def test_complex_filename_with_multiple_dots(self):
        """Test handling filenames with multiple dots."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing file with complex name
            test_file = os.path.join(temp_dir, "my.complex.filename.md")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("existing content")
            
            # Mock user input to decline overwrite
            with patch('builtins.input', return_value='n'):
                result = get_safe_output_filename(test_file)
                expected = os.path.join(temp_dir, "my.complex.filename_1.md")
                assert result == expected
    
    def test_filename_without_extension(self):
        """Test handling filenames without extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing file without extension
            test_file = os.path.join(temp_dir, "filename_no_ext")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("existing content")
            
            # Mock user input to decline overwrite
            with patch('builtins.input', return_value='n'):
                result = get_safe_output_filename(test_file)
                expected = os.path.join(temp_dir, "filename_no_ext_1")
                assert result == expected
    
    @patch('pdfsources.__main__.logger')
    def test_logging_alternative_filename(self, mock_logger):
        """Test that alternative filename is logged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing file
            test_file = os.path.join(temp_dir, "existing.md")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("existing content")
            
            # Mock user input to decline overwrite
            with patch('builtins.input', return_value='n'):
                result = get_safe_output_filename(test_file)
                expected = os.path.join(temp_dir, "existing_1.md")
                
                # Verify logging was called
                mock_logger.info.assert_called_with(f"Using alternative filename: {expected}")
                assert result == expected