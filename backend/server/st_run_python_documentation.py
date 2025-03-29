import ast
import os
from datetime import datetime

import streamlit as st
from openai import Client

from nebius_demos.python_documentation_assistant import document_python_code
from nebius_demos.python_documentation_assistant.connection import submit_record
from nebius_demos.python_documentation_assistant.utils.utils import (
    DEFAULT_MODEL_CHECKPOINT,
)


BASE_URL = (
    os.getenv("NEBIUS_BASE_URL")
    or os.getenv("OPENAI_BASE_URL")
    or "https://api.studio.nebius.ai/v1"
)
API_KEY = os.getenv("NEBIUS_API_KEY") or os.getenv("OPENAI_API_KEY")
if API_KEY is None:
    raise ValueError(
        "Please provide the API key to Nebius AI Studio with `NEBIUS_API_KEY=...` or `OPENAI_API_KEY=...`"
    )

st.set_page_config(page_title="Annotate the Functions in Your Code", layout="wide")

if st.session_state.get("COUNTER") is None:
    st.session_state["COUNTER"] = 0

# Store the output in session state to persist between reruns
if "current_output" not in st.session_state:
    st.session_state.current_output = ""
if "in_time" not in st.session_state:
    st.session_state.in_time = None
if "init_code" not in st.session_state:
    st.session_state.init_code = ""


def main():
    col1, col2 = st.columns(2)
    client = Client(api_key=API_KEY, base_url=BASE_URL)
    with col1:
        st.title("Input your Python code here:")
        init_code = st.text_area("Input Code", height=450, key="input_code")
        document_button = st.button("Document my code!")
        modify_existing_documentation = st.checkbox(
            "Modify existing content", value=False
        )
        do_write_arguments_annotations = st.checkbox(
            "Write arguments annotations", value=True
        )
        do_write_docstrings = st.checkbox("Write docstrings", value=True)
        do_write_comments = st.checkbox("Write comments", value=True)
        model_checkpoint = st.text_input(
            "Model checkpoint to use", DEFAULT_MODEL_CHECKPOINT
        )
        if model_checkpoint == DEFAULT_MODEL_CHECKPOINT:
            model_checkpoint = None

    with col2:
        title_placeholder = st.empty()
        title_placeholder.title(" ")  # Empty title for alignment
        output_placeholder = st.empty()

        _update_streamlit_output(
            output_placeholder=output_placeholder, output=init_code
        )
        thank_you_placeholder = st.empty()

        if document_button and init_code:
            # Make the code `raw` to avoid bugs with `ast`
            code = rf"{init_code}"
            # Empty the "thank you" text
            thank_you_placeholder = st.empty()
            in_time = datetime.now()
            # Save input to database
            submit_record(table="inputs", in_time=in_time, in_code=code)

            title_placeholder.empty()  # Remove title during annotation
            title_placeholder.title("Annotating your code...")
            try:
                for output in document_python_code(
                    code=code,
                    client=client,
                    modify_existing_documentation=modify_existing_documentation,
                    do_write_arguments_annotation=do_write_arguments_annotations,
                    do_write_docstrings=do_write_docstrings,
                    do_write_comments=do_write_comments,
                    in_time=in_time,
                    model_checkpoint=model_checkpoint,
                ):
                    _update_streamlit_output(
                        output_placeholder=output_placeholder, output=output
                    )
            except Exception as e:
                st.error(e)
                import sys, pdb

                exc_type, exc_value, exc_traceback = sys.exc_info()
                pdb.post_mortem(exc_traceback)
            title_placeholder.title(" ")
            st.session_state.init_code = init_code
            st.session_state.in_time = in_time
            st.session_state.current_output = output

        # Always show the last output if it exists
        if len(st.session_state.current_output):
            _update_streamlit_output(
                output_placeholder=output_placeholder,
                output=st.session_state.current_output,
            )
            # Show feedback buttons after output is displayed
            feedback = st.feedback(options="thumbs")
            if feedback is not None:
                thank_you_placeholder.success("Thank you for your feedback!")
                submit_record(
                    table="feedback",
                    in_code=st.session_state.init_code,
                    out_code=st.session_state.current_output,
                    in_time=st.session_state.in_time,
                    out_time=datetime.now(),
                    is_good=bool(feedback),
                )


def _update_streamlit_output(output_placeholder: st._DeltaGenerator, output: str):
    st.session_state["COUNTER"] += 1
    output_placeholder.text_area(
        "Output Code",
        value=output,
        height=450,
        key=f"output_code_{st.session_state['COUNTER']}",
    )


if __name__ == "__main__":
    main()
