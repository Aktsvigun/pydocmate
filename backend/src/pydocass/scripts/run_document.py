#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime
import tempfile

from pydocass.core.document_python_code import document_python_code
from pydocass.connection import submit_record
from pydocass.utils.utils import format_code_with_black, get_client
from pydocass.utils.constants import DEFAULT_MODEL_CHECKPOINT


def document_file(
    input_file: str | None = None,
    code: str | None = None,
    output_file: str | None = None,
    modify_existing_documentation: bool = True,
    do_write_arguments_annotations: bool = True,
    do_write_docstrings: bool = True,
    do_write_comments: bool = True,
    use_streaming: bool = False,
    annotate_with_any: bool = False,
    model_checkpoint: str | None = None,
    api_key: str | None = None,
    verbose: bool = False,
):
    """
    Document a Python file or code string and return the documented code.

    Args:
        input_file: Path to the Python file to document. If None, the code parameter must be provided.
        code: Python code string to document. If None, the input_file parameter must be provided.
        output_file: Path to write the documented code. If None, the documented code is returned.
        modify_existing_documentation: Whether to modify existing documentation.
        do_write_arguments_annotations: Whether to write argument annotations.
        do_write_docstrings: Whether to write docstrings.
        do_write_comments: Whether to write comments.
        use_streaming: Whether to use streaming for the documentation process.
        annotate_with_any: Whether to annotate with any.
        model_checkpoint: Model checkpoint to use. If None, uses the default.
        api_key: API key for Nebius AI Studio or OpenAI. If None, uses environment variables.
        verbose: Whether to show progress updates during the documentation process.

    Returns:
        The documented code as a string.

    Raises:
        FileNotFoundError: If the input file is not found.
        Exception: If there's an error during the documentation process.
    """
    # Read the input code if not provided directly
    if code is None:
        if input_file is None:
            raise ValueError("Either input_file or code must be provided.")
        try:
            with open(input_file, "r") as f:
                code = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file '{input_file}' not found")
        except Exception as e:
            raise Exception(f"Error reading input file: {str(e)}")

    try:
        # Record input for tracking
        in_time = datetime.now()
        submit_record(table="inputs", in_time=in_time, in_code=code)

        # Get the OpenAI/Nebius client
        client = get_client({"api_key": api_key})

        # Process the code
        documented_code = None

        if verbose:
            print("Starting documentation process...", file=sys.stderr)

        for chunk in document_python_code(
            code=code,
            client=client,
            modify_existing_documentation=modify_existing_documentation,
            do_write_arguments_annotation=do_write_arguments_annotations,
            do_write_docstrings=do_write_docstrings,
            do_write_comments=do_write_comments,
            use_streaming=use_streaming,
            annotate_with_any=annotate_with_any,
            in_time=in_time,
            model_checkpoint=model_checkpoint,
        ):
            documented_code = chunk
            if verbose:
                print(".", end="", file=sys.stderr, flush=True)

        if verbose:
            print("\nFormatting code with Black...", file=sys.stderr)

        # Format the final code with Black
        documented_code = format_code_with_black(documented_code)

        # Output the documented code if output_file is specified
        if len(documented_code) > 0 and output_file:
            with open(output_file, "w") as f:
                f.write(documented_code)
            if verbose:
                print(f"Documented code written to {output_file}", file=sys.stderr)

        return documented_code

    except Exception as e:
        print(f"Error: {str(e)}\nFile: {input_file}", file=sys.stderr)
        # if output_file:
        #     with open(output_file, 'w') as f:
        #         pass
        import pdb

        exc_type, exc_value, exc_traceback = sys.exc_info()
        pdb.post_mortem(exc_traceback)
        return


def main():
    """Run the documentation assistant from the command line."""
    parser = argparse.ArgumentParser(
        description="PyDocAss - Python Documentation Assistant"
    )

    parser.add_argument(
        "-i",
        "--input-file",
        help="Path to the Python file to document. Use '-' to read from stdin.",
    )

    parser.add_argument(
        "-o",
        "--output-file",
        help="Path to write the documented code. If not provided, will print to stdout.",
    )

    parser.add_argument(
        "--no-modify-existing",
        action="store_false",
        dest="modify_existing_documentation",
        help="Don't modify existing documentation.",
    )

    parser.add_argument(
        "--no-arguments-annotations",
        action="store_false",
        dest="do_write_arguments_annotations",
        help="Don't write argument annotations.",
    )

    parser.add_argument(
        "--no-docstrings",
        action="store_false",
        dest="do_write_docstrings",
        help="Don't write docstrings.",
    )

    parser.add_argument(
        "--no-comments",
        action="store_false",
        dest="do_write_comments",
        help="Don't write comments.",
    )

    parser.add_argument(
        "--use-streaming",
        action="store_true",
        default=False,
        dest="use_streaming",
        help="Use streaming for the documentation process.",
    )

    parser.add_argument(
        "--annotate-with-any",
        action="store_true",
        default=False,
        dest="annotate_with_any",
        help="Annotate with any.",
    )

    parser.add_argument(
        "-m",
        "--model",
        default=None,
        dest="model_checkpoint",
        help=f"Model checkpoint to use. Default: {DEFAULT_MODEL_CHECKPOINT}",
    )

    parser.add_argument(
        "--api-key",
        help="API key for Nebius AI Studio or OpenAI. Can also be set via NEBIUS_API_KEY or OPENAI_API_KEY environment variables.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show progress updates during documentation process.",
    )

    args = parser.parse_args()

    # Handle stdin input
    code = None
    input_file = args.input_file
    if args.input_file == "-":
        code = sys.stdin.read()
        input_file = None

    try:
        # Call the document_file function
        documented_code = document_file(
            input_file=input_file,
            code=code,
            output_file=args.output_file,
            modify_existing_documentation=args.modify_existing_documentation,
            do_write_arguments_annotations=args.do_write_arguments_annotations,
            do_write_docstrings=args.do_write_docstrings,
            do_write_comments=args.do_write_comments,
            use_streaming=args.use_streaming,
            annotate_with_any=args.annotate_with_any,
            model_checkpoint=args.model_checkpoint,
            api_key=args.api_key,
            verbose=args.verbose,
        )

        # If no output file was specified, print to stdout
        if not args.output_file:
            print(documented_code)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
