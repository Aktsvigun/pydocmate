import ast


def maybe_add_class_to_typing_import(
    code: str, class_name: str = "Union"
) -> str:
    tree = ast.parse(code)
    idx_node_from_typing = None
    # Find `from typing import` section
    for i, node in enumerate(tree.body):
        if isinstance(node, ast.ImportFrom) and node.module == "typing":
            if idx_node_from_typing is None:
                idx_node_from_typing = i
            for name in node.names:
                if name.name == class_name:
                    return code
    
    if idx_node_from_typing is None:
        num_line_breaks_after_import = 3 if not isinstance(tree.body[0], (ast.Import, ast.ImportFrom)) else 1
        code = f"from typing import {class_name}" + "\n" * num_line_breaks_after_import + code
        return code
    
    # In this case, there is `from typing import` section, but the `class_name` is not in the `names` list.
    # Hence, we need to add it.
    node_from_typing = tree.body[idx_node_from_typing]
    start_line = node_from_typing.lineno - 1
    end_line = node_from_typing.end_lineno
    
    # Get the lines containing the import statement
    import_lines = code.splitlines()[start_line:end_line]
    import_text = '\n'.join(import_lines)
    
    # Handle single-line imports: from typing import Type1, Type2
    if len(import_lines) == 1:
        # Insert the new class before the end of the line
        if import_text.strip().endswith(')'):
            # It's a single line with parentheses: from typing import (Type1, Type2)
            modified_import = import_text.replace(')', f', {class_name})')
        else:
            # Regular single line: from typing import Type1, Type2
            modified_import = import_text + f", {class_name}"
    # Handle multi-line imports: from typing import (Type1, Type2)
    else:
        # Check if the import uses parentheses
        if '(' in import_text and ')' in import_text:
            # Find the line with the closing parenthesis
            for i, line in enumerate(import_lines):
                if ')' in line:
                    # Add the new class before the closing parenthesis
                    indent = len(line) - len(line.lstrip())
                    spaces = ' ' * indent
                    import_lines[i] = line.replace(')', f'    {class_name},\n{spaces})')
                    break
            modified_import = '\n'.join(import_lines)
        else:
            # Convert to multi-line format
            modified_import = import_lines[0] + f", {class_name}"
    
    # Replace the import statement in the code
    lines = code.splitlines()
    lines[start_line:end_line] = modified_import.splitlines()
    
    return '\n'.join(lines)
