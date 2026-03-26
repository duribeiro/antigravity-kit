"""
Formatação de saída e nomenclatura de arquivos do Memory Miner.
"""

import re
from pathlib import Path

from models import Session, STOPWORDS


# ---------------------------------------------------------------------------
# Renderização Markdown
# ---------------------------------------------------------------------------

def render_markdown(session: Session, session_id: str) -> str:
    """Serializa a Session para o formato Raw-First em Markdown."""
    header = (
        f"# Sessão: {session.date}\n"
        f"**Canal:** {session.channel} | **Modelo:** {session.model} | **Sessão:** {session_id}\n\n"
        "---\n\n"
    )

    blocks = []
    for msg in session.messages:
        caller = "Eduardo" if msg.role == "user" else "Agente"
        blocks.append(f"[{msg.timestamp}] **{caller}:**\n{msg.text}\n")

    return header + "\n---\n\n".join(blocks)


# ---------------------------------------------------------------------------
# Nomenclatura
# ---------------------------------------------------------------------------

def make_slug(session: Session) -> str:
    """Slug descritivo (máx. 5 palavras) a partir do conteúdo da sessão."""
    user_msgs = [m for m in session.messages if m.role == "user"]
    source = user_msgs[0].text if user_msgs else (session.messages[0].text if session.messages else "")

    # Remove prefixos técnicos do OpenClaw
    source = re.sub(r"\[cron:[^\]]+\]", "", source)
    source = re.sub(r"<[^>]+>", "", source)

    # Extrai a primeira linha com conteúdo real (ignora linhas vazias de tags)
    lines = [L.strip() for L in source.split("\n") if L.strip()]
    source = lines[0] if lines else ""

    words = [
        w for w in re.findall(r"\b[\w\u00c0-\u00ff]+\b", source.lower())
        if w not in STOPWORDS and len(w) > 2
    ]
    slug = "-".join(words[:5])
    return slug[:60] or "sessao"


def make_filename(session: Session, slug: str) -> str:
    """Gera nome de arquivo: YYYY-MM-DD-HH-MM-<slug>."""
    return f"{session.first_ts}-{slug}"


# ---------------------------------------------------------------------------
# IO de notas
# ---------------------------------------------------------------------------

def write_note(content: str, filename: str, dest: Path) -> Path:
    """Salva a nota com anti-colisão de nomes."""
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{filename}.md"
    counter = 1
    while path.exists():
        path = dest / f"{filename}-{counter}.md"
        counter += 1
    path.write_text(content, encoding="utf-8")
    return path
