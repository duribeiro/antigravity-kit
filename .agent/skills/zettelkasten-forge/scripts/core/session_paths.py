"""
Session Paths Module — Zettelkasten Forge
Persiste caminhos de origem/saída em JSON temporário durante a sessão.
Elimina a necessidade de passar --active-dir repetidamente entre scripts.
"""
import json
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Arquivo temporário para armazenar caminhos da sessão atual
_SESSION_FILE = Path(tempfile.gettempdir()) / "forge_session.json"


def save_session(input_dir: str, active_dir: str) -> None:
    """Salva caminhos da sessão no arquivo temporário."""
    data = {
        "input_dir": str(Path(input_dir).resolve()),
        "active_dir": str(Path(active_dir).resolve()),
    }
    _SESSION_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("📍 Sessão salva: %s", _SESSION_FILE)


def load_session() -> dict:
    """Lê caminhos da sessão. Retorna dict vazio se não existir."""
    if not _SESSION_FILE.exists():
        return {}
    try:
        return json.loads(_SESSION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_active_dir(fallback: str | None = None) -> Path | None:
    """Retorna o active_dir da sessão ou do fallback passado via flag."""
    if fallback:
        return Path(fallback).resolve()
    session = load_session()
    if "active_dir" in session:
        logger.info("📍 Usando active_dir da sessão: %s", session["active_dir"])
        return Path(session["active_dir"])
    return None


def get_archive_dir(active_dir: Path) -> Path:
    """Calcula o archive_dir como irmão do active_dir."""
    return active_dir.parent / "archive"


def clear_session() -> None:
    """Remove o arquivo de sessão temporário."""
    if _SESSION_FILE.exists():
        _SESSION_FILE.unlink()
        logger.info("🧹 Sessão temporária removida.")
