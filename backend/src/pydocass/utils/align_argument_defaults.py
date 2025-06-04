import ast
import re

def align_argument_defaults(code: str) -> str:
   """
   Aligns default values in function definitions after type annotations are added.
   """
   tree = ast.parse(code)
   
   class FunctionAligner(ast.NodeVisitor):
       def __init__(self, source_lines):
           self.source_lines = source_lines
           self.modifications = []  # Store (line_no, new_line) tuples
           
       def visit_FunctionDef(self, node):
           self.align_defaults(node)
           self.generic_visit(node)
           
       def visit_AsyncFunctionDef(self, node):
           self.align_defaults(node)
           self.generic_visit(node)

       def visit_ClassDef(self, node):
           self.align_class_attributes(node)
           self.generic_visit(node)
           
       def align_defaults(self, node):
           # Get the function definition lines
           start_line = node.lineno - 1  # Convert to 0-based
           
           # Find the end of the function signature
           # We need to find the closing parenthesis
           lines = []
           current_line = start_line
           paren_count = 0
           found_start = False
           
           while current_line < len(self.source_lines):
               line = self.source_lines[current_line]
               
               # Track parentheses
               for char in line:
                   if char == '(':
                       paren_count += 1
                       found_start = True
                   elif char == ')':
                       paren_count -= 1
               
               lines.append((current_line, line))
               
               if found_start and paren_count == 0:
                   break
                   
               current_line += 1
           
           # Extract parameter lines with defaults
           param_lines = []
           for line_no, line in lines:
               # Check if this line contains a parameter with default value
               if '=' in line and not line.strip().startswith(('@', 'def', 'async')):
                   # But ONLY if we're still in the function signature (before the ':')
                   if ':' in line and line.strip().endswith(':'):
                       # This is the last line of the signature
                       continue
                   # Extract the part before and after '='
                   match = re.match(r'^(\s*)(.*?)(\s*)(=)(\s*)(.*?)(\s*)(,?)(.*)$', line)
                   if match:
                       param_lines.append({
                           'line_no': line_no,
                           'indent': match.group(1),
                           'param_part': match.group(2).rstrip(),
                           'equals': match.group(4),
                           'value_part': match.group(6).lstrip(),
                           'comma': match.group(8),
                           'comment': match.group(9),
                           'original': line
                       })
           
           if not param_lines:
               return
           
           # Find the maximum length of parameter parts
           max_param_length = max(len(p['param_part']) for p in param_lines)
           
           # Reconstruct aligned lines
           for param in param_lines:
               # Calculate spacing needed
               spaces_needed = max_param_length - len(param['param_part'])
               
               # Reconstruct the line with aligned '='
               new_line = (
                   param['indent'] + 
                   param['param_part'] + 
                   ' ' * spaces_needed + 
                   ' = ' +  # Standardize spacing around '='
                   param['value_part'] +
                   param['comma'] +
                   param['comment']
               )
               
               self.modifications.append((param['line_no'], new_line))

       def align_class_attributes(self, node):
           # Get the class definition lines
           start_line = node.lineno - 1  # Convert to 0-based
           end_line = node.end_lineno - 1 if hasattr(node, 'end_lineno') else len(self.source_lines) - 1
           
           # Extract attribute assignment lines
           attr_lines = []
           for line_no in range(start_line + 1, end_line + 1):
               line = self.source_lines[line_no]
               stripped = line.strip()
               # Check if this line contains a simple assignment (not method def)
               # and is not inside a nested function/class
               if ('=' in line and 
                   not stripped.startswith(('def', 'async', '@', 'class')) and
                   not stripped.startswith(('"""', "'''")) and  # Skip docstrings
                   line.count(' ') < 8):  # Simple heuristic to avoid deeply nested code
                   match = re.match(r'^(\s*)(.*?)(\s*)(=)(\s*)(.*?)$', line)
                   if match:
                       attr_lines.append({
                           'line_no': line_no,
                           'indent': match.group(1),
                           'attr_part': match.group(2).rstrip(),
                           'equals': match.group(4),
                           'value_part': match.group(6).rstrip(),
                           'original': line
                       })
           
           if not attr_lines:
               return
           
           # Find the maximum length of attribute parts
           max_attr_length = max(len(a['attr_part']) for a in attr_lines)
           
           # Reconstruct aligned lines
           for attr in attr_lines:
               # Calculate spacing needed
               spaces_needed = max_attr_length - len(attr['attr_part'])
               
               # Reconstruct the line with aligned '='
               new_line = (
                   attr['indent'] + 
                   attr['attr_part'] + 
                   ' ' * spaces_needed + 
                   ' = ' +  # Standardize spacing around '='
                   attr['value_part'] +
                   '\n'
               )
               
               self.modifications.append((attr['line_no'], new_line))
   
   # Split source into lines
   lines = code.splitlines(keepends=True)
   
   # Visit the AST
   aligner = FunctionAligner(lines)
   aligner.visit(tree)
   
   # Apply modifications
   for line_no, new_line in aligner.modifications:
       # Preserve the original line ending
       if lines[line_no].endswith('\n'):
           new_line += '\n'
       lines[line_no] = new_line
   
   return ''.join(lines)
