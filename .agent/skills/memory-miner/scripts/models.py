"""
Tipos de dados e constantes do Memory Miner.
"""

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

OPENCLAW_DIR = ".openclaw"
SESSIONS_DIR = "agents"

STOPWORDS = frozenset(
    {
        "o", "a", "os", "as", "um", "uma", "de", "do", "da", "em",
        "no", "na", "que", "e", "é", "com", "para", "por", "ao",
        "se", "me", "te", "nos", "you", "the", "and", "to", "is",
    }
)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """Mensagem extraída de uma sessão JSONL."""
    role: str          # "user" | "assistant"
    text: str
    timestamp: str     # "YYYY-MM-DD HH:MM" ou "?"


@dataclass
class Session:
    """Sessão OpenClaw parseada com metadados."""
    date: str
    channel: str
    model: str
    first_ts: str = ""  # "YYYY-MM-DD-HH-MM" (para nomear o arquivo)
    messages: list[Message] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.messages) == 0
