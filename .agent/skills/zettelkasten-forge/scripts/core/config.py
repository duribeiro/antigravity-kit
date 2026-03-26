"""
Core Configuration Module (Zettelkasten Forge)
Stores RegEx patterns, constants, and validation rules.
"""
import re

# Valid drawers for knowledge atoms
VALID_CATEGORIES: list[str] = ["decisions", "lessons", "pending", "people", "projects"]

import os

# --- API Configuration ---
# Zero-Trust Security: Chaves sensíveis extraídas de Variáveis de Ambiente (.env / OS)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

LLM_MAX_INPUT_CHARS: int = 100_000
LLM_TEMPERATURE: float = 0.2

# --- Cleanup: Regex Patterns for text purification ---
# Tuple format: (descriptive_name, regex_pattern)
CLEANUP_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "dir_listing_header",
        re.compile(
            r"Mode\s+LastWriteTime\s+Length\s+Name\s*\r?\n"
            r"\s*-+\s+-+\s+-+\s+-+\s*\r?\n"
            r"(?:.*(?:d----|a----).*\r?\n\s*\r?\n)*",
            re.MULTILINE,
        ),
    ),
    (
        "dir_path_line",
        re.compile(r"^.*Diret.rio:.*$", re.MULTILINE),
    ),
    (
        "json_error_block",
        re.compile(r"\{[^{}]*\"error\"[^{}]*\}", re.DOTALL),
    ),
    (
        "json_status_block",
        re.compile(r"\{[^{}]*\"status\"\s*:\s*\"error\"[^{}]*\}", re.DOTALL),
    ),
    (
        "think_tags",
        re.compile(r"<think>[\s\S]*?</think>", re.DOTALL),
    ),
    (
        "successfully_wrote",
        re.compile(r"^.*Successfully wrote \d+ bytes to .*\.md.*$", re.MULTILINE),
    ),
    (
        "no_output",
        re.compile(r"^\(no output\)\s*$", re.MULTILINE),
    ),
    (
        "long_code_blocks",
        re.compile(r"```(?:bash|powershell|shell|cmd)\n(?:(?!```).)*\n```", re.DOTALL),
    ),
    (
        "excessive_blank_lines",
        re.compile(r"\n{4,}"),
    ),
]

# Patterns that need a specific replacement string, not just removal
CLEANUP_REPLACEMENTS: list[tuple[str, re.Pattern, str]] = [
    (
        "collapse_blank_lines",
        re.compile(r"\n{4,}"),
        "\n\n",
    ),
]
