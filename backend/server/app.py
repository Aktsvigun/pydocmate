import os
from datetime import datetime
from argparse import ArgumentParser

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

from pydocass.core.document_python_code import document_python_code
from pydocass.connection import submit_record
from pydocass.utils.utils import format_code_with_black, get_client

import logging

log = logging.getLogger(__name__)


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

USE_STREAMING = True


@app.route("/document", methods=["POST"])
def document_code():
    data = request.json
    code = rf"{data.get('code', '')}"
    in_time = datetime.now()
    try:
        submit_record(table="inputs", in_time=in_time, in_code=code)
    except Exception as e:
        log.error("Error submitting record (non-critical): %s", e)

    client = get_client(data)

    def generate():
        chunk: str = code
        for chunk in document_python_code(
            code=code,
            client=client,
            modify_existing_documentation=data["modify_existing_documentation"],
            do_write_arguments_annotation=data["do_write_arguments_annotations"],
            do_write_docstrings=data["do_write_docstrings"],
            do_write_comments=data["do_write_comments"],
            in_time=in_time,
            model_checkpoint=data["model_checkpoint"],
            use_streaming=USE_STREAMING,
        ):
            yield chunk
        yield format_code_with_black(chunk)

    return Response(stream_with_context(generate()), mimetype="text/plain")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--port", default="4000", type=str, required=False)
    args = parser.parse_args()
    app.run(host="0.0.0.0", port=args.port)
