import unittest
from unittest.mock import MagicMock, patch

from pydocass.core.document_python_code import document_python_code


class TestDocumentPythonCode(unittest.TestCase):
    """Test cases for the document_python_code function."""

    def setUp(self):
        """Set up mock objects for testing."""
        self.mock_client = MagicMock()
        self.mock_tokenizer = MagicMock()

    @patch('pydocass.core.document_python_code._check_no_duplicating_methods')
    @patch('pydocass.core.document_python_code._get_nodes_dict_with_functions_classes_methods')
    @patch('pydocass.core.document_python_code.write_arguments_annotations')
    @patch('pydocass.core.document_python_code.write_docstrings')
    @patch('pydocass.core.document_python_code.write_comments')
    @patch('pydocass.core.document_python_code.submit_record')
    def test_document_python_code_simple(self, mock_submit, mock_comments, mock_docstrings, 
                                         mock_args, mock_nodes, mock_check):
        """Test basic execution of document_python_code function."""
        # Arrange
        mock_nodes.return_value = {}
        mock_args.return_value = ["code with annotations", {}, {}]
        mock_docstrings.return_value = ["code with docstrings", {}]
        mock_comments.return_value = ["code with comments", {}]
        
        # Act
        result = list(document_python_code(
            code="def test(): pass",
            client=self.mock_client,
            tokenizer=self.mock_tokenizer
        ))
        
        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "code with comments")
        mock_submit.assert_called_once()


if __name__ == '__main__':
    unittest.main() 