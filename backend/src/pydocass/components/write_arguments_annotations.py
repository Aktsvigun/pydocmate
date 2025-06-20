import ast
import re
import typing
from typing import Union, Optional
import json

from openai import Client
from pydantic import create_model, Field, BaseModel
from transformers import PreTrainedTokenizerFast

from ..utils.prompts import (
    MESSAGES_ARGUMENTS_ANNOTATION,
    MESSAGES_FIX_ANNOTATION,
    USER_PROMPT,
)
from ..utils.utils import (
    get_valid_json_if_possible,
    get_model_checkpoint_and_params,
    extract_llm_response_data,
)
from ..utils.constants import (
    DEFAULT_TOP_P_ANNOTATIONS,
    DEFAULT_MODEL_CHECKPOINT,
    ANNOTATION_MAX_NUM_NODES_PER_MODEL,
    FORBIDDEN_ARG_NAMES_IN_ANNOTATION,
)
from .write_docstrings import get_docstring_position_for_node_with_no_docstring


TYPING_CLASSES = set(name for name in dir(typing) if name[0].isupper())

POSSIBLE_RETURNS_ANNOTATION_TYPES = (
    ast.Constant,
    ast.Name,
    ast.Subscript,
    ast.Attribute,
    ast.BinOp,
    ast.Tuple,
)

RETURNS_ARGUMENT_NAME_OPTIONS = (
    "returns",
    "function_returns",
    "function_return_annotation",
)


def write_arguments_annotations(
    target_nodes_dict: dict[
        str, tuple[Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef], str]
    ],
    code: str,
    client: Client,
    tokenizer: PreTrainedTokenizerFast,
    modify_existing_documentation: bool = False,
    model_checkpoint: str = DEFAULT_MODEL_CHECKPOINT,
    annotate_with_any: bool = False,
    use_streaming: bool = True,
):
    if use_streaming:
        generation_function = _process_streaming_completion
    else:
        generation_function = _process_non_streaming_completion
    # Create the Pydantic models and get the nodes and args
    models_and_args = _create_pydantic_model_and_get_nodes_args(
        target_nodes_dict, modify_existing_documentation=modify_existing_documentation
    )
    if models_and_args is None:
        # In this case, there are no arguments to annotate
        return
    pydantic_models, all_nodes_with_args = models_and_args

    # Initialize tracking variables
    mutable_vars = {
        "code": code,
        "prev_arg_lineno": 0,
        "shift_inside_line": 0,
        "lines_shift": 0,
    }

    for pydantic_model in pydantic_models:
        user_prompt = str(USER_PROMPT).format(
            code=code, json_schema=pydantic_model.model_json_schema()
        )
        model_checkpoint, max_tokens = get_model_checkpoint_and_params(
            user_prompt=user_prompt,
            tokenizer=tokenizer,
            pydantic_model=pydantic_model,
            task="annotations",
            model_checkpoint=model_checkpoint,
        )
        messages = list(MESSAGES_ARGUMENTS_ANNOTATION) + [
            {"role": "user", "content": user_prompt}
        ]
        yield from generation_function(
            client=client,
            model_checkpoint=model_checkpoint,
            messages=messages,
            max_tokens=max_tokens,
            pydantic_model=pydantic_model,
            all_nodes_with_args=all_nodes_with_args,
            modify_existing_documentation=modify_existing_documentation,
            mutable_vars=mutable_vars,
            annotate_with_any=annotate_with_any,
        )


def _process_streaming_completion(
    client: Client,
    model_checkpoint: str,
    messages: list,
    max_tokens: int,
    pydantic_model: BaseModel,
    all_nodes_with_args: dict,
    modify_existing_documentation: bool,
    mutable_vars: dict[str, int | str],
    annotate_with_any: bool = False,
):
    """Process the completion request using streaming."""
    with client.beta.chat.completions.stream(
        model=model_checkpoint,
        messages=messages,
        top_p=DEFAULT_TOP_P_ANNOTATIONS,
        max_tokens=max_tokens,
        response_format=pydantic_model,
        stream_options={"include_usage": True},
    ) as stream:
        code = mutable_vars["code"]
        prev_arg_lineno = mutable_vars["prev_arg_lineno"]
        shift_inside_line = mutable_vars["shift_inside_line"]
        lines_shift = mutable_vars["lines_shift"]
        output = ""
        output_length = 0
        boundary = 1
        finished_keys = {
            x: set() for x in pydantic_model.model_json_schema()["$defs"].keys()
        }
        required_typing_imports = set()
        for i, chunk in enumerate(stream):
            if hasattr(chunk, "delta"):
                output += chunk.delta
                output_length += len(chunk.delta)
                # Check that a new key has been processed
                for end_pos in range(output_length, boundary, -1):
                    # The output looks smth like `{"ClassKekMethodLol": {"arg1": "list[int]", "ar`
                    if valid_dict := (
                        get_valid_json_if_possible(output[:end_pos] + "}}")
                        or get_valid_json_if_possible(output[:end_pos] + "}}")
                    ):
                        # TODO: stop checking all keys, only do for the last N keys and only if `chunk.delta` length is too large
                        for node_name, node_annotations in valid_dict.items():
                            for key, value in node_annotations.items():
                                if not key in finished_keys[node_name] and value:
                                    # If parts of the annotation belong to the `typing` package, add the imports
                                    required_typing_imports = _potentially_add_typing_import(
                                        value=value,
                                        required_typing_imports=required_typing_imports,
                                    )
                                    # If the annotation is broken
                                    value = _maybe_fix_unclosed_annotation(
                                        value, client, model_checkpoint, max_tokens
                                    )
                                    # Update key value in the code
                                    update_annotation_kwargs = dict(
                                        arg_value=value,
                                        code=code,
                                        modify_existing_documentation=modify_existing_documentation,
                                        prev_arg_lineno=prev_arg_lineno,
                                        shift_inside_line=shift_inside_line,
                                        lines_shift=lines_shift,
                                        annotate_with_any=annotate_with_any,
                                    )
                                    # In this case this is an argument annotation
                                    arg_data = all_nodes_with_args[node_name][1][key][0]
                                    if not (
                                        arg_data is None
                                        or isinstance(
                                            arg_data,
                                            POSSIBLE_RETURNS_ANNOTATION_TYPES,
                                        )
                                    ):
                                        (
                                            code,
                                            prev_arg_lineno,
                                            shift_inside_line,
                                            lines_shift,
                                        ) = _update_argument_annotation_in_code(
                                            arg_data=arg_data,
                                            **update_annotation_kwargs,
                                        )
                                        yield code
                                    else:
                                        code, lines_shift = (
                                            _update_returns_annotation_in_code(
                                                func=all_nodes_with_args[node_name][0],
                                                **update_annotation_kwargs,
                                            )
                                        )
                                        yield code
                                    finished_keys[node_name].add(key)
                boundary = output_length
        response_data = extract_llm_response_data(chunk)
        # Update the mutable variables
        mutable_vars["code"] = code
        mutable_vars["prev_arg_lineno"] = prev_arg_lineno
        mutable_vars["shift_inside_line"] = shift_inside_line
        mutable_vars["lines_shift"] = lines_shift
        yield code, required_typing_imports, response_data


def _process_non_streaming_completion(
    client: Client,
    model_checkpoint: str,
    messages: list,
    max_tokens: int,
    pydantic_model: BaseModel,
    all_nodes_with_args: dict,
    modify_existing_documentation: bool,
    mutable_vars: dict[str, int | str],
    annotate_with_any: bool = False,
):
    """
    Process the completion request without streaming.
    NB! Currently only supported for Anthropic with Instructor syntax
    """
    # Work-around for Anthropic models
    import instructor
    from anthropic import Anthropic
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY", client.api_key)
    client_anthropic = instructor.from_anthropic(client=Anthropic(api_key=api_key))

    code = mutable_vars["code"]
    prev_arg_lineno = mutable_vars["prev_arg_lineno"]
    shift_inside_line = mutable_vars["shift_inside_line"]
    lines_shift = mutable_vars["lines_shift"]

    response = client_anthropic.messages.create(
        model=model_checkpoint,
        messages=messages,
        top_p=DEFAULT_TOP_P_ANNOTATIONS,
        max_tokens=max_tokens,
        response_model=pydantic_model,
    )
    annotations_data = response.dict()

    if not annotations_data:
        # If we couldn't parse the JSON, yield the original code
        yield code
        return

    required_typing_imports = set()

    # For each node in the response
    for node_name, node_annotations in annotations_data.items():
        if node_name not in all_nodes_with_args:
            continue

        for key, value in node_annotations.items():
            if not value:
                continue

            # If parts of the annotation belong to the `typing` package, add the imports
            required_typing_imports = _potentially_add_typing_import(
                value=value, required_typing_imports=required_typing_imports
            )

            # If the annotation is broken
            value = _maybe_fix_unclosed_annotation(
                value, client, model_checkpoint, max_tokens
            )

            # Update key value in the code
            update_annotation_kwargs = dict(
                arg_value=value,
                code=code,
                modify_existing_documentation=modify_existing_documentation,
                prev_arg_lineno=prev_arg_lineno,
                shift_inside_line=shift_inside_line,
                lines_shift=lines_shift,
                annotate_with_any=annotate_with_any,
            )

            # Get the argument data
            arg_data = all_nodes_with_args[node_name][1][key][0]

            # Update the appropriate annotation in the code
            if not (
                arg_data is None
                or isinstance(arg_data, POSSIBLE_RETURNS_ANNOTATION_TYPES)
            ):
                # Update argument annotation
                code, prev_arg_lineno, shift_inside_line, lines_shift = (
                    _update_argument_annotation_in_code(
                        arg_data=arg_data, **update_annotation_kwargs
                    )
                )
            else:
                # Update returns annotation
                code, lines_shift = _update_returns_annotation_in_code(
                    func=all_nodes_with_args[node_name][0], **update_annotation_kwargs
                )

    # Final yield with the updated code and required imports
    response_data = {"model": model_checkpoint, "output": response.model_dump_json()}
    # Current work-around to handle Anthropic limits
    import time

    time.sleep(60)
    # Update the mutable variables
    mutable_vars["code"] = code
    mutable_vars["prev_arg_lineno"] = prev_arg_lineno
    mutable_vars["shift_inside_line"] = shift_inside_line
    mutable_vars["lines_shift"] = lines_shift
    yield code, required_typing_imports, response_data


def _update_argument_annotation_in_code(
    arg_value: str,
    arg_data: Union[ast.arg, ast.AnnAssign, ast.Assign, ast.Subscript],
    code: str,
    prev_arg_lineno: int = 0,
    shift_inside_line: int = 0,
    lines_shift: int = 0,
    modify_existing_documentation: bool = False,
    annotate_with_any: bool = False,
) -> tuple[str, int, int, int]:
    # If the argument is `self`, we don't need to annotate it
    arg_name = (
        arg_data.arg
        if isinstance(arg_data, ast.arg)
        else (
            arg_data.target.id
            if isinstance(arg_data, ast.AnnAssign)
            else arg_data.targets[0].id
        )
    )
    if arg_name == "self":
        return code, prev_arg_lineno, shift_inside_line, lines_shift
    elif arg_value == "Any" and not annotate_with_any:
        return code, prev_arg_lineno, shift_inside_line, lines_shift
    lineno = arg_data.lineno
    lines = code.splitlines()
    if isinstance(arg_data, ast.Assign) or arg_data.annotation is None:
        position = sum(len(line) + 1 for line in lines[: lineno - 1 + lines_shift])
        if isinstance(arg_data, (ast.arg, ast.AnnAssign)):
            position += arg_data.end_col_offset
        else:
            position += arg_data.targets[0].end_col_offset
        if prev_arg_lineno == lineno:
            position += shift_inside_line
            shift_inside_line += len(arg_value) + 2
        else:
            shift_inside_line = len(arg_value) + 2
        code = code[:position] + ": " + arg_value + code[position:]
    elif modify_existing_documentation:
        annotation_start = (
            sum(
                len(line) + 1
                for line in lines[: arg_data.annotation.lineno - 1 + lines_shift]
            )
            + arg_data.annotation.col_offset
        )
        annotation_end = (
            sum(
                len(line) + 1
                for line in lines[: arg_data.annotation.end_lineno - 1 + lines_shift]
            )
            + arg_data.annotation.end_col_offset
        )
        if prev_arg_lineno == lineno:
            annotation_start += shift_inside_line
            annotation_end += shift_inside_line
            shift_inside_line += len(arg_value) + annotation_start - annotation_end
        else:
            shift_inside_line = len(arg_value) + annotation_start - annotation_end
        lines_shift -= arg_data.annotation.end_lineno - arg_data.annotation.lineno
        code = code[:annotation_start] + arg_value + code[annotation_end:]
    return code, lineno, shift_inside_line, lines_shift


def _update_returns_annotation_in_code(
    arg_value: str,
    code: str,
    func: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    modify_existing_documentation: bool = False,
    prev_arg_lineno: int = 0,
    shift_inside_line: int = 0,
    lines_shift: int = 0,
    annotate_with_any: bool = False,
) -> tuple[str, int]:
    if arg_value == "Any" and not annotate_with_any:
        return code, lines_shift

    if func.returns is None:
        docstring_position = get_docstring_position_for_node_with_no_docstring(
            node=func,
            code=code,
            lines_shift=lines_shift,
            prev_arg_lineno=prev_arg_lineno,
            shift_inside_line=shift_inside_line,
        )
        closing_bracket_position = code[:docstring_position].rfind(")") + 1
        code = (
            code[:closing_bracket_position]
            + " -> "
            + arg_value
            + code[closing_bracket_position:]
        )
    # This means the annotation exists
    elif modify_existing_documentation:
        splitlines = code.splitlines()
        start_position = (
            sum(len(l) + 1 for l in splitlines[: func.returns.lineno - 1 + lines_shift])
            + func.returns.col_offset
        )
        end_position = (
            sum(
                len(l) + 1
                for l in splitlines[: func.returns.end_lineno - 1 + lines_shift]
            )
            + func.returns.end_col_offset
        )
        if func.returns.lineno == prev_arg_lineno:
            start_position += shift_inside_line
            end_position += shift_inside_line
        if (
            code[:start_position].strip()[-1] == "("
            and code[end_position:].strip()[0] == ")"
        ):
            new_code = (
                code[:start_position].strip()[:-1]
                + arg_value
                + code[end_position + 1 :].strip()[1:]
            )
        else:
            new_code = (
                code[:start_position].strip()
                + " "
                + arg_value
                + code[end_position:].strip()
            )
        lines_shift -= len(code.strip().splitlines()) - len(new_code.splitlines())
        code = new_code
    return code, lines_shift


def _create_pydantic_model_and_get_args_for_node(
    node_name: str,
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef],
    node_type: str,
    modify_existing_documentation: bool = False,
):
    if node_type == "class":
        node_args = _get_class_args_data(node)
        if node_args is None:
            return
    else:
        node_args = _get_function_or_method_args_data(
            node, is_method=(node_type == "method")
        )
    if node_type in ("class", "function"):
        model_name = f"{node_type.title()}{node_name.title()}"
    elif node_type == "method":
        class_name, method_name = node_name.split("-")
        model_name = f"Class{class_name.title()}Method{method_name.title()}"
    else:
        raise NotImplementedError(f"Unsupported node type: {node_type}")
    # Create a description and potentially default value for each argument
    args_with_field_data = {}
    for arg, arg_data in node_args.items():
        arg_kwargs = {}
        description = f"Annotation of the argument: `{arg}`"
        # Then the default value is not None
        if len(arg_data) == 3:
            description += f" with default value: `{arg_data[2]}`"
            if arg_data[1] is not None:
                # In this case, we should not modify this argument
                if not modify_existing_documentation:
                    continue
                description += f", and current annotation: `{arg_data[1]}`"
                arg_kwargs["default"] = arg_data[1]
        elif arg_data[1] is not None:
            # In this case, we should not modify this argument
            if not modify_existing_documentation:
                continue
            description += f" with current annotation: `{arg_data[1]}`"
            arg_kwargs["default"] = arg_data[1]
        arg_kwargs["description"] = description + "."
        # Fix when arg name starts with "_" (e.g. __tablename__ for a database)
        if arg.startswith("_"):
            arg = "argument" + arg
        args_with_field_data[arg] = arg_kwargs
    # In this case, there are no args to annotate
    if (
        all("default" in v for v in args_with_field_data.values())
        and not modify_existing_documentation
    ):
        args_data = {}
    else:
        args_data = {
            arg: (
                str,
                (
                    Field(**field_data)
                    if "default" in field_data.keys()
                    else Field(..., **field_data)
                ),
            )
            for arg, field_data in args_with_field_data.items()
        }
    if (
        node_type == "class"
        or node_name.endswith("init__")
        or (node.returns is not None and not modify_existing_documentation)
    ):
        # Check that this node needs to be annotated in this case
        if not len(args_data) and not modify_existing_documentation:
            return
        model = create_model(model_name, **args_data)
        return model, node_args
    else:
        node_args_names = set(node_args.keys())
        returns_argument_name = next(
            x for x in RETURNS_ARGUMENT_NAME_OPTIONS if not x in node_args_names
        )
        # Do the same for the `return` argument if this is not a class or an in-built method
        return_kwargs = {
            "description": "Return type annotation. This is the type hint that appears after the `->`"
        }
        returns_annotation = None
        if node.returns is not None:
            # Check that this node needs to be annotated in this case
            if not len(args_data) and not modify_existing_documentation:
                return
            returns_annotation = ast.unparse(node.returns)
            return_kwargs["default"] = returns_annotation
            return_kwargs[
                "description"
            ] += f". Current annotation: `{returns_annotation}`"
        return_kwargs["description"] += "."
        node_args[returns_argument_name] = (node.returns, returns_annotation)
    args_data, node_args = _fix_unavailable_arg_names(args_data, node_args)

    model = create_model(
        model_name,
        **args_data,
        **{returns_argument_name: (str, Field(**return_kwargs))},
    )
    return model, node_args


def _create_pydantic_model_and_get_nodes_args(
    target_nodes_dict: dict[
        str, tuple[Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef], str]
    ],
    modify_existing_documentation: bool = False,
    max_num_nodes_per_model: int = ANNOTATION_MAX_NUM_NODES_PER_MODEL,
) -> Optional[
    tuple[
        list[type[BaseModel]],
        dict[
            str,
            tuple[
                Union[ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef],
                dict[
                    str,
                    tuple[
                        Union[ast.arg, ast.AnnAssign, ast.Assign, ast.Constant, None],
                        str | None,
                    ]
                    | tuple[Union[ast.arg, ast.AnnAssign, ast.Assign], str | None, str],
                ],
            ],
        ],
    ]
]:
    node_models = []
    all_nodes_and_args = {}
    for node_name, (node, node_type) in target_nodes_dict.items():
        model_and_args = _create_pydantic_model_and_get_args_for_node(
            node_name=node_name,
            node=node,
            node_type=node_type,
            modify_existing_documentation=modify_existing_documentation,
        )
        if model_and_args is not None:
            node_model, node_args = model_and_args
            all_nodes_and_args[node_model.__name__] = (node, node_args)
            node_models.append(node_model)
    if (num_nodes := len(node_models)) == 0:
        return
    elif num_nodes <= max_num_nodes_per_model:
        fields = {model.__name__: (model, ...) for model in node_models}
        pydantic_model = create_model("ArgumentsModel", **fields)
        # Return a list for type consistency
        return [pydantic_model], all_nodes_and_args
    # Otherwise, we need to create several models
    pydantic_models = []
    for i in range(0, num_nodes, max_num_nodes_per_model):
        batch = node_models[i : i + max_num_nodes_per_model]
        batch_fields = {model.__name__: (model, ...) for model in batch}
        pydantic_model = create_model(f"ArgumentsModel", **batch_fields)
        pydantic_models.append(pydantic_model)
    return pydantic_models, all_nodes_and_args


def _arguments_without_annotation_exist(func_args_data: list[ast.arg]) -> bool:
    for arg in func_args_data:
        if arg.annotation is None:
            return True
    return False


def _get_class_args_data(
    class_node: ast.ClassDef,
) -> (
    dict[
        str,
        tuple[Union[ast.AnnAssign, ast.Assign], str | None]
        | tuple[Union[ast.AnnAssign, ast.Assign], str | None, str | None],
    ]
    | None
):
    """
    1. Check that __init__ method exists. If so, it is superior and will be annotated later.
    2. If no __init__ method is found, check for ann_assign arguments
    3. If nothing is found, then the class is an inheritance class and doesn't have arguments
    :param class_node:
    :return:
    """
    node_args = {}
    for subnode in class_node.body:
        if isinstance(subnode, (ast.AnnAssign, ast.Assign)):
            annotation = None
            if isinstance(subnode, ast.AnnAssign) and subnode.annotation:
                annotation = ast.unparse(subnode.annotation)
            arg_name = (
                subnode.target.id
                if isinstance(subnode, ast.AnnAssign)
                else subnode.targets[0].id
            )
            if arg_name.startswith("_"):
                arg_name = "argument" + arg_name
            if (default := subnode.value) is not None:
                default = ast.unparse(default)
                node_args[arg_name] = (subnode, annotation, default)
            else:
                node_args[arg_name] = (subnode, annotation)
        if isinstance(subnode, ast.FunctionDef) and subnode.name == "__init__":
            return
    return node_args


def _get_function_or_method_args_data(
    node: ast.FunctionDef | ast.AsyncFunctionDef, is_method: bool = False
) -> dict[
    str,
    tuple[Union[ast.arg, None], str | None] | tuple[ast.arg, str | None, str | None],
]:
    node_args = {}
    for arg in node.args.args:
        name = arg.arg
        if name.startswith("_"):
            name = "argument" + name
        annotation = ast.unparse(arg.annotation) if arg.annotation else None
        arg_index = node.args.args.index(arg)
        default_offset = len(node.args.args) - len(node.args.defaults)
        # Find default value if it exists
        if arg_index >= default_offset:
            default = ast.unparse(node.args.defaults[arg_index - default_offset])
            node_args[name] = (arg, annotation, default)
        else:
            node_args[name] = (arg, annotation)
    # If it is a method, differentiate between `staticmethod`s and others
    if is_method:
        # Check it is a `staticmethod`
        if len(decorator_list := node.decorator_list) and any(
            ast.unparse(decorator) == "staticmethod" for decorator in decorator_list
        ):
            return node_args
        # Otherwise, remove the first argument since it is `self` (even if it is named differently)
        first_arg = list(node_args.keys())[0]
        node_args.pop(first_arg)
    return node_args


def _potentially_add_typing_import(
    value: str, required_typing_imports: set[str]
) -> set[str]:
    # e.g. value = Any
    if value in TYPING_CLASSES:
        required_typing_imports.add(value)
        return required_typing_imports
    # e.g. value = dict[str, Any] -> inner_values_in_typing_classes = [Any]
    inner_values_in_typing_classes = [x for x in TYPING_CLASSES if ("[" + x) in value]
    for inner_value in inner_values_in_typing_classes:
        required_typing_imports.add(inner_value)
    # e.g. value = Optional[Union[dict[str, Any], int]] -> outer_values_in_typing_classes = [Optional, Union]
    outer_values_in_typing_classes = [x for x in TYPING_CLASSES if (x + "[") in value]
    for outer_value in outer_values_in_typing_classes:
        required_typing_imports.add(outer_value)
    return required_typing_imports


def _maybe_fix_unclosed_annotation(
    value: str, client: Client, model_checkpoint: str, max_tokens: int = 1024
):
    if value.count("[") != value.count("]") or value.count("(") != value.count(")"):
        print("Fixing unclosed annotation. Current annotation:\n" + value)
        messages = list(MESSAGES_FIX_ANNOTATION) + [{"role": "user", "content": value}]
        resp = client.beta.chat.completions.parse(
            model=model_checkpoint,
            messages=messages,
            top_p=0.5,
            max_tokens=max_tokens,
            response_format=PythonAnnotationFixModel,
        )
        value = resp.choices[0].message.content
        value = json.dumps(json.loads(value))
    return value


class PythonAnnotationFixModel(BaseModel):
    fixed_annotation: str = Field(description="Fixed annotation of the argument.")


def _fix_unavailable_arg_names(args_data: dict, node_args: dict) -> tuple[dict, dict]:
    arg_names = tuple(node_args.keys())
    for arg_name in arg_names:
        if arg_name in FORBIDDEN_ARG_NAMES_IN_ANNOTATION:
            fixed_arg_name = "arg_" + arg_name
            # Using `, None` when `args_data` is empty - e.g. if `modify_existing_documentation` is `False` and all annotations are already present in the code.
            args_data[fixed_arg_name] = args_data.pop(arg_name, None)
            node_args[fixed_arg_name] = node_args.pop(arg_name)
    return args_data, node_args

def align_function_defaults(source_code):
    """
    Aligns default values in function definitions after type annotations are added.
    """
    tree = ast.parse(source_code)
    
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
                # Check if this line contains a simple assignment (not method def)
                if '=' in line and not line.strip().startswith(('def', 'async', '@', 'class')):
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
    lines = source_code.splitlines(keepends=True)
    
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


