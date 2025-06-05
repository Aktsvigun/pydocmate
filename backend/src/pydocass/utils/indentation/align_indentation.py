from typing import Literal

from ..constants import DEFAULT_INDENTATION_TYPE, INDENTATION_2_SPACE, INDENTATION_4_SPACE, INDENTATION_TAB, INDENTATION_INCONSISTENT, INDENTATION_MAP


def align_indentation(code: str, indent_type: Literal["2-space", "4-space", "tab", "inconsistent"]) -> str:
   """
   Aligns the indentation of source code to the specified type.

   Args:
       code: Source code string
       indent_type: One of "2-space", "4-space", "tab", or "inconsistent"

   Returns:
       Source code with aligned indentation
   """
   if indent_type == INDENTATION_INCONSISTENT:
       indent_type = INDENTATION_TAB

   lines = code.splitlines(keepends=True)
   result = []
   
   target_indent = INDENTATION_MAP[indent_type]
   
   # Track if we're inside a multi-line string
   in_triple_single = False
   in_triple_double = False
  
   for line in lines:
    # TODO: Maybe remove fixing within quotes
    #    # Check for triple quotes
    #    if '"""' in line:
    #        in_triple_double ^= (line.count('"""') % 2 == 1)
    #    elif "'''" in line:
    #        in_triple_single ^= (line.count("'''") % 2 == 1)
       
    #    # Skip lines inside multi-line strings or single-line triple-quoted strings
    #    if in_triple_single or in_triple_double:
    #        result.append(line)
    #        continue
           
    #    stripped = line.strip()
    #    if (stripped.startswith(('"""', "'''")) and 
    #        stripped.endswith(('"""', "'''")) and len(stripped) > 6):
    #        result.append(line)
    #        continue
       
       # Process indentation
       if indent_type == INDENTATION_TAB:
           # Replace all leading spaces with tabs
           indent = ""
           content = ""
           space_count = 0
           
           for char in line:
               if char == ' ':
                   space_count += 1
               elif char == '\t':
                   # Convert accumulated spaces to tabs if any
                   indent += '\t' * (space_count // 4)
                   if space_count % 4 >= 2:
                       indent += '\t'
                   space_count = 0
                   indent += '\t'
               else:
                   # Convert final spaces to tabs
                   indent += '\t' * (space_count // 4)
                   if space_count % 4 >= 2:
                       indent += '\t'
                   content = line[len(indent) + space_count:]
                   break
           
           new_line = indent + content
       else:
           # Replace only tabs with spaces (2 or 4)
           space_per_tab = 2 if indent_type == INDENTATION_2_SPACE else 4
           new_line = ""
           for char in line:
               if char == '\t':
                   new_line += ' ' * space_per_tab
               else:
                   new_line += char
       
       result.append(new_line)

   return ''.join(result)
