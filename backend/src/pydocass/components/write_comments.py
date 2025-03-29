import json
from openai import Client
from pydantic import create_model, Field, BaseModel
from typing import Any
from transformers import PreTrainedTokenizerFast

from ..utils.prompts import (
    MESSAGES_COMMENTS,
    USER_PROMPT,
)
from ..utils.utils import (
    get_valid_json_if_possible,
    get_model_checkpoint_max_tokens,
    extract_llm_response_data,
)
from ..utils.constants import DEFAULT_TOP_P_COMMENTS, DEFAULT_MODEL_CHECKPOINT

def write_comments(
    code: str,
    client: Client,
    tokenizer: PreTrainedTokenizerFast,
    modify_existing_documentation: bool = False,
    model_checkpoint: str = DEFAULT_MODEL_CHECKPOINT,
    use_streaming: bool = True,
):
    pydantic_model, lines_dict, splitlines, model_kwargs = _create_pydantic_model(code)
    # We reduced the schema with this "trick" in system prompt to add more examples.
    # Hence, need to match the same format here.
    schema = pydantic_model.model_json_schema()["properties"]
    # For the sake of prompt length, we remove 'redundant' attributes
    schema = {
        key: {
            key2: value2
            for key2, value2 in value.items()
            if key2 in ("default", "description")
        }
        for key, value in schema.items()
    }
    user_prompt = str(USER_PROMPT).format(code=code, json_schema=json.dumps(schema))
    model_checkpoint, max_tokens = get_model_checkpoint_max_tokens(
        user_prompt=user_prompt,
        tokenizer=tokenizer,
        task="comments",
        model_checkpoint=model_checkpoint,
    )
    messages = list(MESSAGES_COMMENTS) + [{"role": "user", "content": user_prompt}]
    # Choose between streaming and non-streaming based on user preference
    if use_streaming:
        yield from _process_streaming_comments(
            client=client,
            model_checkpoint=model_checkpoint,
            messages=messages,
            max_tokens=max_tokens,
            pydantic_model=pydantic_model,
            lines_dict=lines_dict,
            splitlines=splitlines,
            schema=schema,
            code=code,
            modify_existing_documentation=modify_existing_documentation,
        )
    else:
        yield from _process_non_streaming_comments(
            client=client,
            model_checkpoint=model_checkpoint,
            messages=messages,
            max_tokens=max_tokens,
            pydantic_model=pydantic_model,
            lines_dict=lines_dict,
            splitlines=splitlines,
            schema=schema,
            code=code,
            modify_existing_documentation=modify_existing_documentation,
        )


def _process_streaming_comments(
    client: Client,
    model_checkpoint: str,
    messages: list,
    max_tokens: int,
    pydantic_model,
    lines_dict: dict,
    splitlines: list,
    schema: dict,
    code: str,
    modify_existing_documentation: bool,
):
    """Process the comments completion request using streaming."""
    with client.beta.chat.completions.stream(
        model=model_checkpoint,
        messages=messages,
        top_p=DEFAULT_TOP_P_COMMENTS,
        max_tokens=max_tokens,
        response_format=pydantic_model,
        stream_options={"include_usage": True},
    ) as stream:
        output = ""
        output_length = 0
        boundary = 1
        finished_keys = set()
        id_line_in_splitlines = -1
        for i, chunk in enumerate(stream):
            if hasattr(chunk, "delta"):
                output += chunk.delta
                output_length += len(chunk.delta)
                # Check that a new key has been processed
                for end_pos in range(output_length, boundary, -1):
                    if valid_dict := get_valid_json_if_possible(
                        output[:end_pos] + "}"
                    ):
                        for key, value in valid_dict.items():
                            # TODO: optimize here
                            if not key in finished_keys:
                                # The outputted keys will look like `line{id}`
                                line = lines_dict[key]
                                finished_keys.add(key)
                                if value or (
                                    "default" in schema[key]
                                    and modify_existing_documentation
                                ):
                                    (
                                        ids_comment_lines,
                                        line_has_inline_comment,
                                        id_line_in_splitlines,
                                    ) = _find_ids_comments_for_line(
                                        line=line,
                                        splitlines=splitlines,
                                        next_line_index_in_code=id_line_in_splitlines
                                        + 1,
                                    )
                                    # TODO: maybe remove already commented lines from schema if not `modify_existing_documentation`
                                    # If existing comments should not be modified, continue
                                    if (
                                        len(ids_comment_lines) > 0
                                        or line_has_inline_comment
                                    ) and not modify_existing_documentation:
                                        continue
                                    # Insert comment to the code
                                    splitlines, id_line_in_splitlines = (
                                        _update_line_comment_in_code(
                                            new_value=value,
                                            line=line,
                                            splitlines=splitlines,
                                            id_line_in_splitlines=id_line_in_splitlines,
                                            ids_comment_lines=ids_comment_lines,
                                            line_has_inline_comment=line_has_inline_comment,
                                        )
                                    )
                                    code = _restore_code_from_numerated_lines(
                                        splitlines
                                    )
                                    yield code
                                else:
                                    id_line_in_splitlines = splitlines.index(
                                        line, id_line_in_splitlines + 1
                                    )
                boundary = output_length
        response_data = extract_llm_response_data(chunk)
        yield code, response_data


def _process_non_streaming_comments(
    client: Client,
    model_checkpoint: str,
    messages: list,
    max_tokens: int,
    pydantic_model: BaseModel,
    lines_dict: dict,
    splitlines: list,
    schema: dict,
    code: str,
    modify_existing_documentation: bool,
):
    """
    Process the comments completion request without streaming.
    NB! Currently only supported for Anthropic with Instructor syntax
    """
    # Work-around for Anthropic models
    import instructor
    from anthropic import Anthropic
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY", client.api_key)
    client_anthropic = instructor.from_anthropic(client=Anthropic(api_key=api_key))
    response = client_anthropic.messages.create(
        model=model_checkpoint,
        messages=messages,
        top_p=DEFAULT_TOP_P_COMMENTS,
        max_tokens=max_tokens,
        response_model=pydantic_model,
    )
    comments_data = response.dict()
    
    if not comments_data:
        # If we couldn't parse the JSON, yield the original code
        yield code
        return
    
    id_line_in_splitlines = -1
    
    # Process all comments at once
    for key, value in comments_data.items():
        if key not in lines_dict:
            continue
            
        # Get the line to add the comment to
        line = lines_dict[key]
        
        if value or ("default" in schema[key] and modify_existing_documentation):
            # Find the location of comments for this line
            ids_comment_lines, line_has_inline_comment, id_line_in_splitlines = _find_ids_comments_for_line(
                line=line,
                splitlines=splitlines,
                next_line_index_in_code=id_line_in_splitlines + 1,
            )
            
            # If existing comments should not be modified, continue
            if (len(ids_comment_lines) > 0 or line_has_inline_comment) and not modify_existing_documentation:
                continue
                
            # Insert comment to the code
            splitlines, id_line_in_splitlines = _update_line_comment_in_code(
                new_value=value,
                line=line,
                splitlines=splitlines,
                id_line_in_splitlines=id_line_in_splitlines,
                ids_comment_lines=ids_comment_lines,
                line_has_inline_comment=line_has_inline_comment,
            )
        else:
            id_line_in_splitlines = splitlines.index(line, id_line_in_splitlines + 1)
    
    # Generate the final code with all comments
    code = _restore_code_from_numerated_lines(splitlines)
    
    # Create response data from the usage info
    response_data = {
        "model": model_checkpoint,
        "output": response.model_dump_json()
    }
    
    # Current work-around to handle Anthropic limits
    import time; time.sleep(60)
    # Yield the final code with all comments added
    yield code, response_data


def _get_lined_code_and_lines(code: str) -> tuple[list[str], dict[str, str], list[str]]:
    """
    Processes the input code to add line numbers to valid lines and identify docstrings.

    Args:
        code (`str`):
            The input code as a string.

    Returns:
        `tuple[list[str], dict[str, str], list[str]]`:
            A tuple containing the modified lines with line numbers, a dictionary mapping line numbers to lines, and a list of valid code lines with line numbers.
    """
    # Split the input code into individual lines
    lines = code.splitlines()
    # Initialize a list to store valid code lines
    valid_code_lines = []
    # Initialize a counter for line numbers
    counter = 1
    # Flag to check if a docstring is currently open
    docstring_is_open = False
    # Variable to store the type of docstring (triple quotes)
    docstring_type = None
    # Iterate over each line in the code with line numbers
    for i, line in enumerate(lines, 1):
        # Check if the line is not empty, not a comment, not a docstring, and not inside a docstring
        if (
            # Strip whitespace from the line
            len(line_stripped := line.strip())
            # Check if the line does not start with a comment symbol
            and (line_stripped[0] != "#")
            # Check if the line is not a docstring
            and (not line_stripped in ['"""', "'''"])
            # Check if a docstring is not currently open
            and (not docstring_is_open)
        ):
            # Add line number to the line
            lined_line = f"{counter}. {line}"
            # Add the line with line number to the list of valid code lines
            valid_code_lines.append(lined_line)
            # Update the original lines list with the line number
            lines[i - 1] = lined_line
            # Increment the line number counter
            counter += 1
        # Check if the line is a docstring
        elif line_stripped in ['"""', "'''"]:
            # Set the type of docstring if it's not already set
            if docstring_type is None:
                docstring_type = line_stripped
            # Check if the current line matches the type of docstring that was opened
            if docstring_type == line_stripped:
                # Toggle the docstring_is_open flag
                docstring_is_open = bool(1 - docstring_is_open)
            # Handle nested docstrings
            else:
                # Then it is a docstring inside a docstring
                pass
    # Create a dictionary mapping line numbers to lines
    lines_dict = {f"line{i}": line for i, line in enumerate(valid_code_lines, 1)}
    return lines, lines_dict, valid_code_lines


def _create_kwargs_for_pydantic_model(
    lines: list[str], valid_lines: list[str]
) -> dict[str, tuple[type, Any]]:
    """
    Creates keyword arguments for a Pydantic model based on the lines of code and valid lines.

    Args:
        lines (`list[str]`):
            The lines of code with line numbers.
        valid_lines (`list[str]`):
            The valid lines of code with line numbers.

    Returns:
        `dict[str, tuple[type, Any]]`:
            A dictionary of keyword arguments for the Pydantic model.
    """
    # Join the lines back into a single string
    lined_code = "\n".join(lines)
    # Initialize a dictionary to store keyword arguments for the Pydantic model
    model_kwargs = {}
    # Split the lined code back into individual lines
    code_lines = lined_code.splitlines()
    # Initialize the index for the next line in the code
    next_line_index_in_code = 0
    # Iterate over each valid line with line numbers
    for i, line in enumerate(valid_lines, 1):
        # Find comments associated with the line
        comment, next_line_index_in_code = _find_comments_for_line(
            line, code_lines, next_line_index_in_code
        )
        # Create keyword arguments for the line
        # Changed from `Comment for the line n. X` to `Comment for line X`
        # to reduce the number of tokens in prompt (~ by 1000)
        line = ". ".join(line.split(". ")[1:])
        line = line.split("#")[0].rstrip()
        line_kwargs = {"description": f"Comment for line {i}: {line}"}
        # Check if there is a comment for the line
        if comment:
            # Add the comment as a default value in the keyword arguments
            line_kwargs["default"] = comment
        # Add the keyword arguments to the model_kwargs dictionary
        model_kwargs[f"line{i}"] = (str, Field(**line_kwargs))
    return model_kwargs


def _create_pydantic_model(
    code: str,
) -> tuple[Any, dict[str, str], list[str], dict[str, tuple[type, Any]]]:
    """
    Creates a Pydantic model for the given code, along with additional information about the lines.

    Args:
        code (`str`):
            The input code as a string.

    Returns:
        `tuple[Any, dict[str, str], list[str], dict[str, tuple[type, Any]]]`:
            A tuple containing the Pydantic model, a dictionary mapping line numbers to lines, the modified lines with line numbers, and the keyword arguments for the Pydantic model.
    """
    # Get the lined code and valid lines from the input code
    lines, lines_dict, valid_lines = _get_lined_code_and_lines(code)
    # Create keyword arguments for the Pydantic model
    model_kwargs = _create_kwargs_for_pydantic_model(lines, valid_lines)
    return (
        # Create the Pydantic model with the keyword arguments
        create_model("CodeCommentsModel", **model_kwargs),
        lines_dict,
        lines,
        model_kwargs,
    )


def _find_comments_for_line(
    line: str, splitlines: list[str], next_line_index_in_code: int = 0
) -> tuple[str, int]:
    """
    Finds comments associated with a specific line of code.

    Args:
        line (`str`):
            The line of code to find comments for.
        splitlines (`list[str]`):
            The lines of code split into a list.
        next_line_index_in_code (`int`, *optional*):
            The index to start searching for comments from. Defaults to 0.

    Returns:
        `tuple[str, int]`:
            A tuple containing the comment text and the index of the line after the last comment.
    """
    # Initialize an empty string to store the comment
    comment = ""
    # Find the index of the line in the splitlines list
    id_line_in_splitlines = splitlines.index(line, next_line_index_in_code)
    # Check for comments above the string
    for code_line in splitlines[next_line_index_in_code:id_line_in_splitlines]:
        # Check if the line is a comment
        if code_line.strip().startswith("#"):
            # Add the comment to the comment string
            comment += code_line[code_line.find("#") + 1 :].strip() + "\\n"
    # Check if there is an inline comment in the line
    if "#" in line and (comment_start_idx := _find_inline_comment(line)) is not None:
        # Make sure it is a comment and not part of the string (e.g. prev. line `if "#" in line`)
        comment += line[comment_start_idx + 1 :].strip()
    # Strip whitespace from the comment
    comment = comment.strip()
    # Check if the comment ends with a newline character
    if comment.endswith("\\n"):
        # Remove the newline character from the comment
        comment = comment[:-2]
    return comment, id_line_in_splitlines + 1


def _find_ids_comments_for_line(
    line: str, splitlines: list[str], next_line_index_in_code: int = 0
) -> tuple[list[int], bool, int]:
    """
    Finds the indices of lines that contain comments for a specific line of code.

    Args:
        line (`str`):
            The line of code to find comments for.
        splitlines (`list[str]`):
            The lines of code split into a list.
        next_line_index_in_code (`int`, *optional*):
            The index to start searching for comments from. Defaults to 0.

    Returns:
        `tuple[list[int], bool, int]`:
            A tuple containing the list of indices of comment lines, a boolean indicating if the line has an inline comment, and the index of the line in splitlines.
    """
    # Initialize a list to store the indices of comment lines
    ids_comment_lines = []
    # Find the index of the line in the splitlines list
    id_line_in_splitlines = splitlines.index(line, next_line_index_in_code)
    # Find previous valid line
    id_prev_line = next_line_index_in_code
    for i, prev_line in enumerate(
        splitlines[next_line_index_in_code:id_line_in_splitlines][::-1], start=1
    ):
        if prev_line.split(". ")[0].isdigit() or prev_line.strip() == '"""':
            id_prev_line = id_line_in_splitlines - i
            break
    # Check for comments above the string
    for i, code_line in enumerate(splitlines[id_prev_line:id_line_in_splitlines]):
        # Check if the line is a comment
        if code_line.strip().startswith("#"):
            # Add the index of the comment line to the list
            ids_comment_lines.append(i + id_prev_line)
    # Flag to check if the line has an inline comment
    line_has_inline_comment = False
    # Check if there is an inline comment in the line
    if "#" in line and _find_inline_comment(line) is not None:
        line_has_inline_comment = True
    return ids_comment_lines, line_has_inline_comment, id_line_in_splitlines


def _update_line_comment_in_code(
    new_value: str,
    line: str,
    splitlines: list[str],
    id_line_in_splitlines: int,
    ids_comment_lines: list[int],
    line_has_inline_comment: bool,
) -> tuple[list[str], int]:
    """
    Updates the comment for a specific line of code in the list of lines.

    Args:
        new_value (`str`):
            The new comment text.
        line (`str`):
            The line of code to update the comment for.
        splitlines (`list[str]`):
            The lines of code split into a list.
        id_line_in_splitlines (`int`):
            The index of the line in splitlines.
        ids_comment_lines (`list[int]`):
            The list of indices of comment lines.
        line_has_inline_comment (`bool`):
            A boolean indicating if the line has an inline comment.

    Returns:
        `tuple[list[str], int]`:
            A tuple containing the updated list of lines and the index of the line after the last comment.
    """
    # Remove the line number from the line
    line_without_number = ". ".join(line.split(". ")[1:])
    # Check if the line starts with a space
    if line_without_number.startswith(" "):
        # Determine the indentation of the line
        indent = " " * (len(line_without_number) - len(line_without_number.lstrip()))
    # Check if the line starts with a tab
    elif line_without_number.startswith("\t"):
        # Determine the indentation of the line
        indent = "\t" * (len(line_without_number) - len(line_without_number.lstrip()))
    # Handle lines with no indentation
    else:
        indent = ""
    # Add the new comment to the line with the appropriate indentation
    if new_value:
        new_value = [indent + "# " + x for x in new_value.split("\n")]
    # Check if there are multiple comment lines
    if len(ids_comment_lines) > 1:
        # Iterate over the comment lines
        for subline in splitlines[ids_comment_lines[0] : ids_comment_lines[-1]]:
            # Strip whitespace from the line
            stripped_line = subline.strip()
            # Assert that the line is either empty or a comment and does not start with a digit
            assert (not len(stripped_line) or stripped_line.startswith("#")) and not (
                subline and subline[0].isdigit()
            )
    # Check if there are any comment lines
    if ids_comment_lines:
        # Assert that the last comment line is before the current line
        assert ids_comment_lines[-1] < id_line_in_splitlines
    # Check if the line has an inline comment
    if line_has_inline_comment:
        # Find the starting index of the inline comment
        comment_start_idx = _find_inline_comment(line)
        # Remove the inline comment from the line
        splitlines[id_line_in_splitlines] = line[:comment_start_idx].rstrip()
    # Check if there are any comment lines
    if ids_comment_lines:
        # Get the code before the comment lines
        previous_code = splitlines[: ids_comment_lines[0]]
    # Handle lines with no comment lines
    else:
        # Get the code before the current line
        previous_code = splitlines[:id_line_in_splitlines]
    # Create the new splitlines list with the updated comment
    if new_value:
        new_splitlines = previous_code + new_value + splitlines[id_line_in_splitlines:]
    else:
        new_splitlines = previous_code + splitlines[id_line_in_splitlines:]
    return new_splitlines, len(previous_code) + len(new_value)


def _restore_code_from_numerated_lines(splitlines: list[str]) -> str:
    """
    Restores the original code from the numerated lines.

    Args:
        splitlines (`list[str]`):
            The lines of code split into a list with line numbers.

    Returns:
        `str`:
            The original code as a string.
    """
    # Initialize a list to store the original lines
    original_lines = []
    # Iterate over each line in the splitlines list
    for line in splitlines:
        # Split the line into two parts at the first '. '
        splitted_line = line.split(". ", 1)
        # Check if the line has a line number
        if len(splitted_line) > 1 and splitted_line[0].isdigit():
            # Remove the line number from the line
            original_lines.append(". ".join(splitted_line[1:]))
        # Handle lines with no line number
        else:
            original_lines.append(line)
    return "\n".join(original_lines)


def _find_inline_comment(line: str) -> int | None:
    """
    Finds the starting index of an inline comment if it exists.

    Args:
        line (`str`):
            The line of code to check.

    Returns:
        `int | None`:
            Index where the comment starts, or None if no comment exists.
    """
    # Flag to check if inside a single quote
    in_single_quote = False
    # Flag to check if inside a double quote
    in_double_quote = False
    # Flag to check if the previous character was an escape character
    escaped = False

    # Iterate over each character in the line with its index
    for i, char in enumerate(line):
        # Handle escape sequences
        if char == "\\":
            # Toggle the escaped flag
            escaped = not escaped
            continue

        # Check if the current character is an escape character
        if escaped:
            # Toggle the escaped flag
            escaped = False
            continue

        # Handle quotes
        if char == '"' and not in_single_quote:
            # Toggle the double quote flag
            in_double_quote = not in_double_quote
        # Check if the current character is a single quote
        elif char == "'" and not in_double_quote:
            # Toggle the single quote flag
            in_single_quote = not in_single_quote
        # Check for comment symbol outside of quotes
        elif char == "#" and not in_single_quote and not in_double_quote:
            # Make sure it's not part of a string that starts later
            rest_of_line = line[i + 1 :]
            # Check if the current character is a comment symbol and not inside quotes
            if not (
                rest_of_line.strip().startswith("'")
                or
                # Check if the rest of the line does not start with a single or double quote
                rest_of_line.strip().startswith('"')
            ):
                return i

    return None
