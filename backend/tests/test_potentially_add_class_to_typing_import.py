import unittest
import ast
from pydocass.components.potentially_add_class_to_typing_import import potentially_add_class_to_typing_import


class TestPotentiallyAddClassToTypingImport(unittest.TestCase):

    def test_class_already_imported(self):
        """Test when the class is already imported from typing."""
        code = "from typing import List, Union, Dict\n\ndef func(): pass"
        result = potentially_add_class_to_typing_import(code, class_name="Union")
        self.assertEqual(result, code)  # Should be unchanged

    def test_no_typing_import(self):
        """Test when there's no typing import at all."""
        code = "import os\n\ndef func(): pass"
        expected = "from typing import Union\n\nimport os\n\ndef func(): pass"
        result = potentially_add_class_to_typing_import(code, class_name="Union")
        self.assertEqual(result, expected)
    
    def test_single_line_import(self):
        """Test adding to a single-line typing import."""
        code = "from typing import List, Dict\n\ndef func(): pass"
        expected = "from typing import List, Dict, Union\n\ndef func(): pass"
        result = potentially_add_class_to_typing_import(code, class_name="Union")
        self.assertEqual(result, expected)
    
    def test_single_line_import_with_parentheses(self):
        """Test adding to a single-line typing import with parentheses."""
        code = "from typing import (List, Dict)\n\ndef func(): pass"
        expected = "from typing import (List, Dict, Union)\n\ndef func(): pass"
        result = potentially_add_class_to_typing_import(code, class_name="Union")
        self.assertEqual(result, expected)
    
    def test_multi_line_import(self):
        """Test adding to a multi-line typing import."""
        code = """from typing import (
    List,
    Dict
)

def func(): pass"""
        expected = """from typing import (
    List,
    Dict,
    Union
)

def func(): pass"""
        result = potentially_add_class_to_typing_import(code, class_name="Union")
        self.assertEqual(result, expected)
    
    def test_multi_line_import_with_different_indentation(self):
        """Test adding to a multi-line typing import with different indentation."""
        code = """from typing import (
  List,
  Dict
)

def func(): pass"""
        expected = """from typing import (
  List,
  Dict,
  Union
)

def func(): pass"""
        result = potentially_add_class_to_typing_import(code, class_name="Union")
        self.assertEqual(result, expected)
    
    def test_import_with_trailing_comma(self):
        """Test adding to an import that already has a trailing comma."""
        code = """from typing import (
    List,
    Dict,
)

def func(): pass"""
        expected = """from typing import (
    List,
    Dict,
    Union,
)

def func(): pass"""
        result = potentially_add_class_to_typing_import(code, class_name="Union")
        self.assertEqual(result, expected)
    
    def test_different_class_name(self):
        """Test adding a different class name."""
        code = "from typing import List, Dict\n\ndef func(): pass"
        expected = "from typing import List, Dict, Optional\n\ndef func(): pass"
        result = potentially_add_class_to_typing_import(code, class_name="Optional")
        self.assertEqual(result, expected)
    
    def test_typing_import_with_alias(self):
        """Test when there's a typing import with an alias."""
        code = "from typing import List as L, Dict\n\ndef func(): pass"
        expected = "from typing import List as L, Dict, Union\n\ndef func(): pass"
        result = potentially_add_class_to_typing_import(code, class_name="Union")
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main() 