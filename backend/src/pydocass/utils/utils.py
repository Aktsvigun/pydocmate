import ast
from datetime import datetime
import json
import os
from typing import Union, Literal, Any
from transformers import PreTrainedTokenizerFast, AutoTokenizer
import warnings
import black

from openai import Client
from openai.lib.streaming.chat._events import ChunkEvent

from .constants import (
    NUM_SYSTEM_PROMPT_TOKENS_DICT,
    MAX_MAX_TOTAL_TOKENS,
    MAX_TOTAL_TOKENS,
    DEFAULT_MAX_TOKENS_DICT,
    DEFAULT_MODEL_CHECKPOINT,
    LONG_CONTEXT_MODEL_CHECKPOINT,
    MAX_TOKENS_FOR_LONG_CONTEXT,
    DEFAULT_TOKENIZER_CHECKPOINT,
    BASE_URL,
)

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def get_valid_json_if_possible(string: str):
    try:
        return json.loads(string)
    except ValueError as e:
        return False


def ast_parse_stable(string: str):
    try:
        return ast.parse(string)
    except SyntaxError as e:
        string = string.replace('\n"\n', '\\n"\n').replace('\t"\n')
        print(string)
        return ast.parse(string)


def get_nodes_dict_with_functions_classes_methods(
    nodes: list[ast.AST],
) -> dict[str, tuple[Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef], str]]:
    target_nodes = {}
    for node in nodes:
        if hasattr(node, "name"):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                target_nodes[node.name] = (node, "function")
            elif isinstance(node, (ast.ClassDef)):
                target_nodes[node.name] = (node, "class")
            else:
                raise ValueError("Unexpected node type:", type(node))
            if isinstance(node, ast.ClassDef):
                for subnode in node.body:
                    if hasattr(subnode, "name"):
                        target_nodes[node.name + "-" + subnode.name] = (
                            subnode,
                            "method",
                        )
    return target_nodes


def check_no_duplicating_methods(nodes: list[ast.AST]):
    functions_names = []
    classes_names = []
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions_names.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes_names.append(node.name)
            class_methods_names = []
            for subnode in node.body:
                if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    class_methods_names.append(subnode.name)
            if len(set(class_methods_names)) != len(class_methods_names):
                for method in class_methods_names:
                    if class_methods_names.count(method) != 1:
                        raise ValueError(
                            f"Method {method} is duplicated for class {node.name}."
                            + "Please fix this before running annotation."
                        )

    if len(set(functions_names)) != len(functions_names):
        for func in functions_names:
            if functions_names.count(func) != 1:
                raise ValueError(
                    f"Function {func} is duplicated."
                    + "Please fix this before running annotation."
                )
    if len(set(classes_names)) != len(classes_names):
        for class_ in classes_names:
            if classes_names.count(class_) != 1:
                raise ValueError(
                    f"Class {class_} is duplicated."
                    + "Please fix this before running annotation."
                )


def get_model_checkpoint_max_tokens(
    user_prompt: str,
    tokenizer: PreTrainedTokenizerFast,
    task: Literal["annotations", "docstrings", "comments"],
    model_checkpoint: str | None = None,
):
    num_user_prompt_tokens = len(tokenizer.tokenize(user_prompt))
    num_system_prompt_tokens = NUM_SYSTEM_PROMPT_TOKENS_DICT[task]
    min_max_tokens = DEFAULT_MAX_TOKENS_DICT[task]
    max_tokens = MAX_TOTAL_TOKENS - num_user_prompt_tokens - num_system_prompt_tokens
    if max_tokens < min_max_tokens:
        warnings.warn(
            "The input is too large. Consider splitting it into several parts. The context will be dillated to fit into the model, which can lead to quality degradation."
        )
        model_checkpoint = model_checkpoint or LONG_CONTEXT_MODEL_CHECKPOINT
        use_extended_prompt = False
        max_tokens = MAX_TOKENS_FOR_LONG_CONTEXT
    elif (
        task == "docstrings"
        and max_tokens
        < min_max_tokens + NUM_SYSTEM_PROMPT_TOKENS_DICT["docstrings_addition"]
    ):
        use_extended_prompt = False
        model_checkpoint = model_checkpoint or DEFAULT_MODEL_CHECKPOINT
    else:
        max_tokens = min(max_tokens, MAX_MAX_TOTAL_TOKENS)
        use_extended_prompt = True
        model_checkpoint = model_checkpoint or DEFAULT_MODEL_CHECKPOINT
        if task == "docstrings":
            max_tokens -= NUM_SYSTEM_PROMPT_TOKENS_DICT["docstrings_addition"]
    if task == "docstrings":
        return model_checkpoint, max_tokens, use_extended_prompt
    return model_checkpoint, max_tokens


def extract_llm_response_data(chunk: ChunkEvent):
    return {
        "id": chunk.chunk.id,
        "created_at": datetime.fromtimestamp(
            chunk.chunk.created or chunk.snapshot.created
        ),
        "model": chunk.chunk.model,
        "completion_tokens": chunk.chunk.usage.completion_tokens,
        "prompt_tokens": chunk.chunk.usage.prompt_tokens,
        "output": chunk.snapshot.choices[0].message.content,
    }


def load_tokenizer(model_checkpoint: str) -> PreTrainedTokenizerFast:
    cache_dir = os.getenv("HF_HOME", None)
    try:
        return AutoTokenizer.from_pretrained(model_checkpoint, cache_dir=cache_dir, use_fast=True)
    except:
        return AutoTokenizer.from_pretrained(
            DEFAULT_TOKENIZER_CHECKPOINT, cache_dir=cache_dir, use_fast=True
        )


def format_code_with_black(code: str) -> str:
    try:
        formatted_code = black.format_str(code, mode=black.Mode())
        return formatted_code
    except black.NothingChanged:
        return code  # Return original code if Black doesn't modify it
    except Exception as e:
        print(f"Error formatting code with Black: {e}")
        return code  # Return original code if an error occurs


def get_client(data: dict[str, Any]):
    api_key = (
        data.get("api_key", None)
        or os.getenv("NEBIUS_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    if api_key is None:
        raise ValueError(
            "Please provide the API key to Nebius AI Studio with `NEBIUS_API_KEY=...` or `OPENAI_API_KEY=...`"
        )

    return Client(api_key=api_key, base_url=BASE_URL)
