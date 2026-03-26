"""
FileSystem and formatting utilities for Zettelkasten Forge.
Strict separation of pure I/O from Business Logic.
"""
import re
from pathlib import Path


def obsidian_link(filename: str) -> str:
    """Gets the internal link format for obsidian: [[filename]]"""
    name = Path(filename).stem
    return f"[[{name}]]"

def slugify(text: str) -> str:
    """Creates a URL-safe filename from text."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

def extract_tags(content: str) -> set[str]:
    """
    Finds all valid hashtags in the content markdown.
    Excludes hex codes like #FFF or #1234.
    """
    # Requires at least one letter inside the tag (ignores #112)
    tag_pattern = re.compile(r"#([a-zA-Záéíóúçãõ][\w\-]*)(?=\s|$|\n|[,;])", re.IGNORECASE)
    matches = tag_pattern.findall(content)
    return set(matches)

def get_file_content(path: Path) -> str:
    """Safe read of utf-8 content."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return ""

def list_latest_md_files(directory: Path, limit: int = 10) -> list[Path]:
    """
    Returns the most recently modified .md files in a directory.
    """
    if not directory.exists():
        return []

    files = [f for f in directory.rglob("*.md")]
    # sort by last modified time, descending
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]
