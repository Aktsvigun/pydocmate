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

    # Define the target indentation character(s)
    
    target_indent = INDENTATION_MAP[indent_type]

    for line in lines:
        # Skip empty lines
        if not line.strip():
            result.append(line)
            continue
        
        # Find the indentation level
        indent_level = 0
        i = 0
        
        while i < len(line):
            if line[i] == '\t':
                indent_level += 1
                i += 1
            elif line[i] == ' ':
                # Count consecutive spaces
                space_count = 0
                while i < len(line) and line[i] == ' ':
                    space_count += 1
                    i += 1
                
                # Convert spaces to indent levels
                # Assume 4 spaces = 1 indent level by default
                # But if we see 2 spaces consistently, treat 2 spaces = 1 indent level
                if space_count >= 4:
                    indent_level += space_count // 4
                    if space_count % 4 >= 2:
                        indent_level += 1
                elif space_count >= 2:
                    indent_level += 1
            else:
                # Reached non-whitespace character
                break
        
        # Reconstruct the line with the target indentation
        content = line.lstrip()
        new_line = target_indent * indent_level + content
        result.append(new_line)

    return ''.join(result)
