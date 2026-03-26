"""
Parsing de sessões JSONL do OpenClaw.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import Message, Session


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _parse_ts(value, date_only: bool = False) -> Optional[str]:
    """Converte timestamp ISO/unix para string formatada."""
    if not value:
        return None
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            if value > 10**12:
                value /= 1000
            dt = datetime.fromtimestamp(value)
        return dt.strftime("%Y-%m-%d" if date_only else "%Y-%m-%d %H:%M")
    except (ValueError, OSError, OverflowError):
        return None


def _detect_channel(content: list) -> Optional[str]:
    """Detecta o canal de comunicação a partir dos parts da mensagem."""
    for part in content:
        if not isinstance(part, dict):
            continue

        text = part.get("text", "")
        if "[cron:" in text:
            return "cron"
        if '"source": "whatsapp"' in text or "source: whatsapp" in text.lower():
            return "whatsapp"
        if '"channelId"' in text:
            return "discord"

        # Detecção via tool call com target numérico (Discord channel ID)
        if part.get("name") == "message":
            target = part.get("arguments", {}).get("target", "")
            if isinstance(target, str) and target.isdigit():
                return "discord"

    return None


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def parse_session(jsonl_path: Path) -> Session:
    """Extrai dados de uma sessão JSONL em uma Session estruturada."""
    session = Session(date="", channel="terminal", model="?")

    with open(jsonl_path, encoding="utf-8") as f:
        for raw_line in f:
            try:
                entry = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            kind = entry.get("type", "")

            if kind == "session":
                session.date = _parse_ts(entry.get("timestamp"), date_only=True) or ""
                continue

            if kind == "model_change":
                session.model = entry.get("modelId", "?")
                continue

            if kind != "message":
                continue

            msg = entry.get("message", {})
            role = msg.get("role", "")
            if role not in ("user", "assistant"):
                continue

            content = msg.get("content", [])

            # Atualiza canal se detectado nesta mensagem
            detected = _detect_channel(content)
            if detected:
                session.channel = detected

            # Extrai texto puro
            parts = [
                p.get("text", "").strip()
                for p in content
                if isinstance(p, dict) and p.get("type") == "text" and p.get("text", "").strip()
            ]
            if not parts:
                continue

            # Timestamp desta mensagem
            ts_raw = entry.get("timestamp") or msg.get("timestamp")
            ts = _parse_ts(ts_raw) or "?"

            # Captura YYYY-MM-DD-HH-MM da 1ª mensagem para nomear o arquivo
            if not session.first_ts and ts_raw:
                full_ts = _parse_ts(ts_raw)  # "YYYY-MM-DD HH:MM"
                if full_ts and len(full_ts) == 16:
                    hh_mm = full_ts[11:].replace(":", "-")
                    session.first_ts = f"{full_ts[:10]}-{hh_mm}"

            # Fallback de data da sessão
            if not session.date and ts_raw:
                session.date = _parse_ts(ts_raw, date_only=True) or ""

            session.messages.append(Message(role=role, text="\n".join(parts), timestamp=ts))

    # Fallback final: mtime do arquivo
    if not session.date:
        mtime = jsonl_path.stat().st_mtime
        dt = datetime.fromtimestamp(mtime)
        session.date = dt.strftime("%Y-%m-%d")
        session.first_ts = dt.strftime("%Y-%m-%d-%H-%M")

    # Garante que first_ts é preenchido mesmo sem timestamp nas mensagens
    if not session.first_ts and session.date:
        session.first_ts = f"{session.date}-00-00"

    return session
