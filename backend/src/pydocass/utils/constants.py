import os

DEFAULT_MODEL_CHECKPOINT = "Qwen/Qwen3-32B-fast"
LONG_CONTEXT_MODEL_CHECKPOINT = "deepseek-ai/DeepSeek-V3-0324-fast"
DEFAULT_TOKENIZER_CHECKPOINT = "Qwen/Qwen3-32B"

MAX_TOTAL_TOKENS = 40_000
MAX_TOKENS_FOR_LONG_CONTEXT = 8_192
MAX_MAX_TOKENS = 16_384

NUM_SYSTEM_PROMPT_TOKENS_DICT = {
    "annotations": 12756,
    "docstrings": 13753,
    "docstrings_addition": 6103,
    "comments": 14108,
}

DEFAULT_MAX_TOKENS_DICT = {"annotations": 2048, "docstrings": 4096, "comments": 2048}
MAX_MAX_TOKENS_DICT = {"annotations": 2048, "docstrings": 4096, "comments": 2048}

DEFAULT_TOP_P_ANNOTATIONS = 0.5
DEFAULT_TOP_P_DOCSTRINGS = 0.01
DEFAULT_TOP_P_COMMENTS = 0.01

DEFAULT_INDENTATION_TYPE = "tab"
INDENTATION_2_SPACE = "2-space"
INDENTATION_4_SPACE = "4-space"
INDENTATION_TAB = "tab"
INDENTATION_INCONSISTENT = "inconsistent"
INDENTATION_MAP = {
    INDENTATION_2_SPACE: "  ",
    INDENTATION_4_SPACE: "    ",
    INDENTATION_TAB: "\t"
}

BASE_URL = (
    os.getenv("NEBIUS_BASE_URL")
    or os.getenv("OPENAI_BASE_URL")
    or "https://api.studio.nebius.ai/v1"
)

ANNOTATION_MAX_NUM_NODES_PER_MODEL = 15

FORBIDDEN_ARG_NAMES_IN_ANNOTATION = ["self", "cls", "model_config"]
