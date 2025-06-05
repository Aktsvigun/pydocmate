from typing import Literal

from ..constants import DEFAULT_INDENTATION_TYPE, INDENTATION_2_SPACE, INDENTATION_4_SPACE, INDENTATION_TAB, INDENTATION_INCONSISTENT


def detect_indentation(code: str ) -> Literal["2-space", "4-space", "tab", "inconsistent"]:
   """
   Detects the indentation style used in source code.
   Returns: "2-space", "4-space", "tab", or "inconsistent"
   """
   lines = code.splitlines()
   
   # Track what types of indentation we've seen
   has_2_space = False
   has_4_space = False
   has_tab = False
   has_other_space = False
   
   for line in lines:
       # Skip empty lines and lines with no indentation
       if not line or not line[0].isspace():
           continue
           
       # Count leading whitespace
       indent = ""
       for char in line:
           if char in ' \t':
               indent += char
           else:
               break
       
       if not indent:
           continue
           
       # Check for tabs
       if '\t' in indent:
           has_tab = True
       
       # Check for spaces
       if ' ' in indent:
           # Count consecutive spaces from the start
           space_count = 0
           for char in indent:
               if char == ' ':
                   space_count += 1
               else:
                   break
           
           # Check what increment of spaces we have
           if space_count > 0:
               if space_count % 4 == 0:
                   has_4_space = True
               elif space_count % 2 == 0:
                   has_2_space = True
               else:
                   has_other_space = True
   
   if (has_4_space or has_2_space) and has_tab:
       return INDENTATION_INCONSISTENT
   elif has_4_space:
       return INDENTATION_4_SPACE
   elif has_2_space:
       return INDENTATION_2_SPACE
   elif has_tab:
       return INDENTATION_TAB
   elif has_other_space:
       return INDENTATION_INCONSISTENT
   else:
       # No indentation found
       return DEFAULT_INDENTATION_TYPE
