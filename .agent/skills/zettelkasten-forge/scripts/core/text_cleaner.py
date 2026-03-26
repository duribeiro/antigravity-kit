"""
Machado Parser.
Applies Regex rules to completely eliminate technical garbage from raw memory logs.
SRP (Single Responsibility Principle): Text Processing Only.
"""
import re
from .config import CLEANUP_PATTERNS, CLEANUP_REPLACEMENTS

def clean_text(raw_text: str) -> tuple[str, dict[str, int]]:
    """
    Applies regex patterns to remove or replace technical noise.

    Args:
        raw_text: The dirty, raw session log content.

    Returns:
        tuple[str, dict]: The cleaned text, and a metrics dictionary with hit counts.
    """
    stats: dict[str, int] = {}
    cleaned = raw_text

    # Apply pure removals
    for name, pattern in CLEANUP_PATTERNS:
        matches = pattern.findall(cleaned)
        if matches:
            stats[name] = len(matches)
            cleaned = pattern.sub("", cleaned)

    # Apply replacements
    for name, pattern, replacement in CLEANUP_REPLACEMENTS:
        matches = pattern.findall(cleaned)
        if matches:
            stats[f"replace_{name}"] = len(matches)
            cleaned = pattern.sub(replacement, cleaned)

    # Clear trailing speaker headers (e.g., "**Aria:**" left hanging)
    hanging_header_pattern = re.compile(r"^\*\*Aria:\*\*\s*\n(?=\s*\n|\s*\*\*)", re.MULTILINE)
    cleaned = hanging_header_pattern.sub("", cleaned)

    return cleaned.strip(), stats
