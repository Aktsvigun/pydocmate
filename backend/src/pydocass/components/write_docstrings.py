import ast
from typing import Union, Literal
from pydantic import create_model, Field, BaseModel
import warnings
import numpy as np
from transformers import PreTrainedTokenizer

from openai import Client

from ..utils.prompts import (
    MESSAGES_DOCSTRING,
    MESSAGES_DOCSTRING_ADDITION,
    USER_PROMPT,
)
from ..utils.utils import (
    get_valid_json_if_possible,
    get_model_checkpoint_max_tokens,
    extract_llm_response_data,
)
from ..utils.constants import DEFAULT_TOP_P_DOCSTRINGS, DEFAULT_MODEL_CHECKPOINT

def write_docstrings(
    target_nodes_dict: dict[
        str, tuple[Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef], str]
    ],
    code: str,
    client: Client,
    tokenizer: PreTrainedTokenizer,
    modify_existing_documentation: bool = False,
    model_checkpoint: str = DEFAULT_MODEL_CHECKPOINT,
    use_streaming: bool = True,
):
    if not modify_existing_documentation:
        existing_docstrings = [
            _extract_docstring(node)
            for node_name, (node, _) in target_nodes_dict.items()
        ]
        target_nodes_dict = {
            k: v
            for (k, v), docstring in zip(target_nodes_dict.items(), existing_docstrings)
            if docstring is None
        }
        if len(target_nodes_dict) == 0:
            return code

    pydantic_model = _create_pydantic_model(target_nodes_dict)
    user_prompt = str(USER_PROMPT).format(
        code=code, json_schema=pydantic_model.model_json_schema()
    )
    model_checkpoint, max_tokens, use_extended_prompt = (
        get_model_checkpoint_max_tokens(
            user_prompt=user_prompt,
            tokenizer=tokenizer,
            task="docstrings",
            model_checkpoint=model_checkpoint,
        )
    )
    messages = _create_messages(use_extended_prompt)
    messages += [{"role": "user", "content": user_prompt}]
    
    # Choose between streaming and non-streaming based on user preference
    if use_streaming:
        yield from _process_streaming_docstrings(
            client=client,
            model_checkpoint=model_checkpoint,
            messages=messages,
            max_tokens=max_tokens,
            pydantic_model=pydantic_model,
            code=code,
            target_nodes_dict=target_nodes_dict,
        )
    else:
        yield from _process_non_streaming_docstrings(
            client=client,
            model_checkpoint=model_checkpoint,
            messages=messages,
            max_tokens=max_tokens,
            pydantic_model=pydantic_model,
            code=code,
            target_nodes_dict=target_nodes_dict,
        )


def _process_streaming_docstrings(
    client: Client,
    model_checkpoint: str,
    messages: list,
    max_tokens: int,
    pydantic_model: BaseModel,
    code: str,
    target_nodes_dict: dict,
):
    """Process the docstrings completion request using streaming."""
    with client.beta.chat.completions.stream(
        model=model_checkpoint,
        messages=messages,
        top_p=DEFAULT_TOP_P_DOCSTRINGS,
        max_tokens=max_tokens,
        response_format=pydantic_model,
        stream_options={"include_usage": True},
    ) as stream:
        output = ""
        output_length = 0
        boundary = 1
        finished_keys = set()
        lines_shift = 0
        for i, chunk in enumerate(stream):
            if hasattr(chunk, "delta"):
                output += chunk.delta
                output_length += len(chunk.delta)
            # Check that a new key has been processed
            for end_pos in range(output_length, boundary, -1):
                if valid_dict := get_valid_json_if_possible(output[:end_pos] + "}"):
                    for key, value in valid_dict.items():
                        if not key in finished_keys and value:
                            # The outputted keys will be function_{func_name} or class_{class_name}
                            # We need to remove the prefix when querying the key
                            func = _get_function_by_key(key, target_nodes_dict)
                            # Replace the generated \t / \n symbols and add tabulation to all lines
                            value = (
                                value.replace("\\\\n", "\n")
                                .replace("\\\\t", "\t")
                                .replace("\\n", "\n")
                                .replace("\\t", "\t")
                            )
                            num_tabs_to_use = (
                                code.splitlines()[func.lineno + lines_shift - 1]
                                .replace(" " * 4, "\t")
                                .count("\t")
                                + 1
                            )
                            joiner = "\n" + "\t" * num_tabs_to_use
                            value = "".join(joiner + x for x in value.split("\n"))
                            old_code = code
                            # Insert docstring to the code
                            code = _update_code_with_node_docstring(
                                generated_docstring=value,
                                function=func,
                                code=code,
                                lines_shift=lines_shift,
                                num_tabs_to_use=num_tabs_to_use,
                            )
                            yield code
                            # Need to adjust since we are adding new lines to parsed code
                            lines_shift += len(code.splitlines()) - len(
                                old_code.splitlines()
                            )
                            finished_keys.add(key)
            boundary = output_length
        response_data = extract_llm_response_data(chunk)
        yield code, response_data


def _process_non_streaming_docstrings(
    client: Client,
    model_checkpoint: str,
    messages: list,
    max_tokens: int,
    pydantic_model: BaseModel,
    code: str,
    target_nodes_dict: dict,
):
    """
    Process the docstrings completion request without streaming.
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
        top_p=DEFAULT_TOP_P_DOCSTRINGS,
        max_tokens=max_tokens,
        response_model=pydantic_model,
    )
    docstrings_data = response.dict()

    if not docstrings_data:
        # If we couldn't parse the JSON, yield the original code
        yield code
        return
    
    lines_shift = 0
    
    # Process all docstrings at once
    for key, value in docstrings_data.items():
        if not value:
            continue
            
        # Get the function or class to add the docstring to
        func = _get_function_by_key(key, target_nodes_dict)
        
        # Format the docstring with proper line breaks and tabs
        value = (
            value.replace("\\\\n", "\n")
            .replace("\\\\t", "\t")
            .replace("\\n", "\n")
            .replace("\\t", "\t")
        )
        
        num_tabs_to_use = (
            code.splitlines()[func.lineno + lines_shift - 1]
            .replace(" " * 4, "\t")
            .count("\t")
            + 1
        )
        
        joiner = "\n" + "\t" * num_tabs_to_use
        value = "".join(joiner + x for x in value.split("\n"))
        
        # Store the old code to calculate the line difference
        old_code = code
        
        # Update the code with the new docstring
        code = _update_code_with_node_docstring(
            generated_docstring=value,
            function=func,
            code=code,
            lines_shift=lines_shift,
            num_tabs_to_use=num_tabs_to_use,
        )
        
        # Update the line shift for the next docstring
        lines_shift += len(code.splitlines()) - len(old_code.splitlines())
    
    # Create response data from the usage info
    response_data = {
        "model": model_checkpoint,
        "output": response.model_dump_json()
    }
    
    # Current work-around to handle Anthropic limits
    import time; time.sleep(60)
    # Yield the final code with all docstrings added
    yield code, response_data


def _update_code_with_node_docstring(
    generated_docstring: str,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    code: str,
    lines_shift: int = 0,
    num_tabs_to_use: int = 1,
) -> str:
    positions = _get_docstring_position(function, code, lines_shift)
    tab = "\t" * num_tabs_to_use
    docstring_to_add = f'\n{tab}"""' + generated_docstring + f'\n{tab}"""\n'
    ending = code[positions[1] :]
    if ending.startswith("\n"):
        ending = ending[1:]
    # For one-line functions, need to add a tabulation
    if function.lineno == function.end_lineno:
        function_def_line = code.splitlines()[function.lineno - 1 + lines_shift]
        if function_def_line.startswith(" "):
            tab = (len(function_def_line) - len(function_def_line.lstrip()) + 4) * " "
        elif function_def_line.startswith("\t"):
            tab = (len(function_def_line) - len(function_def_line.lstrip()) + 1) * "\t"
        else:
            tab = "\t"
        ending = tab + ending.lstrip()
    return code[: positions[0]].strip() + docstring_to_add + ending


def get_docstring_position_for_node_with_no_docstring(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef],
    code: str,
    prev_arg_lineno: int = 0,
    shift_inside_line: int = 0,
    lines_shift: int = 0,
) -> int:
    line_start_function_core_id = node.body[0].lineno - 1 + lines_shift
    border = node.body[0].col_offset
    if prev_arg_lineno == line_start_function_core_id + 1:
        border += shift_inside_line
        # Case 1: single-line function
        if node.body[0].lineno == node.lineno:
            if (lineno := node.lineno) != 0:
                splitlines = code.splitlines()
                len_previous_code = len("\n".join(splitlines[: lineno - 1]))
                border += len_previous_code
            return code[:border].rindex(":") + 1
    # Case 2: multi-line function
    lines = code.splitlines()
    # Lines that pertain to the given node
    lines_cum_length = np.cumsum(
        [len(line) + 1 for line in lines[:line_start_function_core_id]]
    )
    if len(lines_cum_length) >= 1:
        # We take not from the last line because it already points at the function core line
        for i, line in enumerate(
            lines[:line_start_function_core_id][::-1][: len(lines_cum_length)]
        ):
            if not line.strip().startswith("#"):
                break
        border += lines_cum_length[-1 - i]
    index_is_found = False
    while not index_is_found:
        candidate_index = code[:border].rindex(":")
        rev_line_id_candidate = 0
        # Find the line to which this colon (`:`) pertains
        for rev_line_id_candidate, cumsum in enumerate(lines_cum_length[::-1]):
            if cumsum < candidate_index:
                break
        line_id_candidate = line_start_function_core_id - rev_line_id_candidate
        line = lines[line_id_candidate]
        # Make sure this bracket is not inside a comment
        if "#" in line:
            index_of_comment_start = line.find("#")
            if rev_line_id_candidate != 0:
                index_of_comment_start += lines_cum_length[::-1][rev_line_id_candidate]
            if index_of_comment_start < candidate_index:
                border = index_of_comment_start
                continue
        candidate_index += 1
        index_is_found = True
    return candidate_index


def _get_docstring_position(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef],
    code: str,
    lines_shift: int,
) -> Union[tuple[int, int], None]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return

    # If docstring exists
    if (
        node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, (ast.Str, ast.Constant))
    ):
        doc_node = node.body[0]
        lines = code.splitlines()

        # Get start position
        start = sum(
            len(line) + 1 for line in lines[: doc_node.lineno - 1 + lines_shift]
        )
        start += doc_node.col_offset

        # Find the actual end by looking at the source
        if doc_node.lineno == doc_node.end_lineno:
            # Single line docstring
            line = lines[doc_node.lineno - 1 + lines_shift]
            # Find the closing quote
            quote_type = line[doc_node.col_offset : doc_node.col_offset + 3]
            if quote_type in ('"""', "'''"):
                end = line.find(quote_type, doc_node.col_offset + 3) + 3
            else:
                quote_type = line[doc_node.col_offset]
                end = line.find(quote_type, doc_node.col_offset + 1) + 1
            end = start + (end - doc_node.col_offset)
        else:
            # Multi-line docstring
            last_line = lines[doc_node.end_lineno - 1 + lines_shift].rstrip()
            end = sum(
                len(line) + 1 for line in lines[: doc_node.end_lineno - 1 + lines_shift]
            )
            end += len(last_line)

        return start, end

    # If no docstring, return position where it should be
    pos = get_docstring_position_for_node_with_no_docstring(
        node=node, code=code, lines_shift=lines_shift
    )
    return pos, pos


def _extract_docstring(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef],
) -> str | None:
    if (
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and (node.body)
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    ):
        return node.body[0].value.value


def _create_pydantic_model_class(name):
    return {
        "class_"
        + name: (str, Field(..., description=f"Docstring for the class `{name}`"))
    }


def _create_pydantic_model_class_method(class_name, method_name):
    return {
        f"class_{class_name}_method_{method_name}": (
            str,
            Field(
                ...,
                description=f"Docstring for the method `{method_name}` of the class `{class_name}`",
            ),
        )
    }


def _create_pydantic_model_function(name):
    return {
        "function_"
        + name: (str, Field(..., description=f"Docstring for the function `{name}`"))
    }


def _create_pydantic_model(
    nodes_with_types: dict[
        str, tuple[Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef], str]
    ],
) -> BaseModel:

    pydantic_model_kwargs = {}
    for name, (_, type_) in nodes_with_types.items():
        if type_ == "class":
            pydantic_model_kwargs.update(_create_pydantic_model_class(name))
        elif type_ == "method":
            args = name.split("-")
            # Don't annotate the `__init__` methods
            if args[1] == "__init__":
                continue
            pydantic_model_kwargs.update(_create_pydantic_model_class_method(*args))
        elif type_ == "function":
            pydantic_model_kwargs.update(_create_pydantic_model_function(name))
        else:
            print(type_)
            raise NotImplementedError

    return create_model(f"DocstringModel", **pydantic_model_kwargs)


def _create_messages(use_extended_prompt: bool = True) -> list[str, str]:
    if use_extended_prompt:
        return MESSAGES_DOCSTRING + MESSAGES_DOCSTRING_ADDITION
    return MESSAGES_DOCSTRING


def _get_function_by_key(
    key: str,
    target_nodes_dict: dict[
        str, tuple[Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef], str]
    ],
) -> Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]:
    if key.startswith("class_"):
        key = key[len("class_") :]
        if "_method_" in key:
            class_name = key.split("_method_")[0]
            method_name = "_method_".join(key.split("_method_")[1:])
            key = class_name + "-" + method_name
    elif key.startswith("function_"):
        key = key[len("function_") :]
    else:
        raise ValueError("Unexpected key:", key)
    return target_nodes_dict[key][0]
