import ast
import logging
from datetime import datetime
from typing import Generator


from openai import Client
from transformers import PreTrainedTokenizerFast

from ..components import (
    write_docstrings,
    write_arguments_annotations,
    write_comments,
    maybe_add_class_to_typing_import,
)
from ..connection import submit_record
from ..utils.utils import (
    get_nodes_dict_with_functions_classes_methods,
    check_no_duplicating_methods,
    load_tokenizer,
)
from ..utils.indentation import detect_indentation, align_indentation
from ..utils.align_argument_defaults import align_argument_defaults
from ..utils.constants import DEFAULT_MODEL_CHECKPOINT


log = logging.getLogger(__name__)


def document_python_code(
    code: str,
    client: Client,
    modify_existing_documentation: bool = False,
    do_write_arguments_annotation: bool = True,
    do_write_docstrings: bool = True,
    do_write_comments: bool = True,
    use_streaming: bool = True,
    annotate_with_any: bool = False,
    do_align_argument_defaults: bool = False,
    model_checkpoint: str = DEFAULT_MODEL_CHECKPOINT,
    tokenizer: PreTrainedTokenizerFast | None = None,
    in_time: datetime | None = None,
) -> Generator[str, None, None]:
    # Save the initial time for recording purposes
    if in_time is None:
        in_time = datetime.now()
    # Read the code as a raw string to avoid AST parsing errors
    code = rf"{code}"
    # Make copy of the initial code
    in_code = str(code)
    # Get current indentation. It will be one of ["2-space", "4-space", "tab", "inconsistent"]
    indent_type = detect_indentation(code)
    # Parse the code into an AST
    tree = ast.parse(code)

    # Check that there are no duplicate methods, classes, or functions
    check_no_duplicating_methods(tree.body)
    # Get a dictionary of nodes that need to be annotated or documented
    target_nodes_dict = get_nodes_dict_with_functions_classes_methods(tree.body)

    # Load tokenizer to track the number of input tokens
    if tokenizer is None:
        tokenizer = load_tokenizer(model_checkpoint)

    output = None
    # Set default values
    annotations_response_data = {}
    docstrings_response_data = {}
    comments_response_data = {}
    if do_write_arguments_annotation:
        # Annotate the arguments and returns of functions, classes, and methods
        for output in write_arguments_annotations(
            target_nodes_dict=target_nodes_dict,
            code=code,
            client=client,
            tokenizer=tokenizer,
            modify_existing_documentation=modify_existing_documentation,
            model_checkpoint=model_checkpoint,
            use_streaming=use_streaming,
            annotate_with_any=annotate_with_any,
        ):
            if isinstance(output, str):
                yield output
        # Get the required imports from the `typing` package that will need to be added in the end
        if output is not None:
            code, required_typing_imports, annotations_response_data = output
            annotations_response_data["required_imports"] = required_typing_imports
            # If there are classes from the `typing` package that were used for annotation but not imported,
            # add them to the imports
            for typing_class in required_typing_imports:
                code = maybe_add_class_to_typing_import(code, typing_class)
                yield code
            code = align_indentation(code=code, indent_type=indent_type)
            if do_align_argument_defaults:
                code = align_argument_defaults(code=code)
            # Lines may have changed, so it's easier to rerun `ast.parse` which takes < 1ms than track
            # this throughout the code
            tree = ast.parse(code)
            # Get dictionary with target nodes with the updated AST code
            target_nodes_dict = get_nodes_dict_with_functions_classes_methods(tree.body)

    if do_write_docstrings:
        output = None
        # Add docstrings to functions, classes, and methods
        for output in write_docstrings(
            target_nodes_dict=target_nodes_dict,
            code=code,
            client=client,
            tokenizer=tokenizer,
            modify_existing_documentation=modify_existing_documentation,
            model_checkpoint=model_checkpoint,
            use_streaming=use_streaming,
        ):
            if isinstance(output, str):
                yield output
        if output is not None:
            code, docstrings_response_data = output
        code = align_indentation(code=code, indent_type=indent_type)

    if do_write_comments:
        # Add comments to the code where necessary
        for output in write_comments(
            code=code,
            client=client,
            tokenizer=tokenizer,
            modify_existing_documentation=modify_existing_documentation,
            model_checkpoint=model_checkpoint,
            use_streaming=use_streaming,
        ):
            if isinstance(output, str):
                yield output
        code, comments_response_data = output
    code = align_indentation(code=code, indent_type=indent_type)
    # Make sure the generated code has valid Python syntax
    ast.parse(code)
    # Save to database
    try:
        submit_record(
            table="responses",
            in_code=in_code,
            out_code=code,
            in_time=in_time,
            out_time=datetime.now(),
            **{"annotations_" + k: v for k, v in annotations_response_data.items()},
            **{"docstrings_" + k: v for k, v in docstrings_response_data.items()},
            **{"comments_" + k: v for k, v in comments_response_data.items()},
        )
    except Exception as e:
        log.error("Error submitting record (non-critical): %s", e)
    yield code
