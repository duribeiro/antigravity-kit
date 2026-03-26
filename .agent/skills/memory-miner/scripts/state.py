"""
Gerenciamento de estado delta e descoberta de agentes do Memory Miner.
"""

import json
from datetime import datetime
from pathlib import Path

from models import OPENCLAW_DIR, SESSIONS_DIR


# ---------------------------------------------------------------------------
# Estado delta
# ---------------------------------------------------------------------------

def _get_skill_state_path() -> Path:
    """Retorna o caminho do arquivo de estado dentro da pasta da skill."""
    # O arquivo fica em ../data/state.json relativo a este script (scripts/state.py)
    path = Path(__file__).parent.parent / "data" / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_state(root: Path) -> set[str]:
    """Carrega lista de sessões já processadas para o projeto específico."""
    path = _get_skill_state_path()
    if not path.exists():
        return set()
    
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        project_key = str(root.resolve())
        return set(data.get("projects", {}).get(project_key, {}).get("processed", []))
    except (json.JSONDecodeError, KeyError):
        return set()


def save_state(root: Path, processed: set[str]) -> None:
    """Persiste o estado delta centralizado na skill."""
    path = _get_skill_state_path()
    project_key = str(root.resolve())
    
    # Carrega estado global existente
    all_data = {"projects": {}}
    if path.exists():
        try:
            all_data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    
    # Atualiza apenas este projeto
    if "projects" not in all_data:
        all_data["projects"] = {}
        
    all_data["projects"][project_key] = {
        "processed": sorted(processed),
        "last_run": datetime.now().isoformat()
    }
    
    path.write_text(json.dumps(all_data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Descoberta de agentes
# ---------------------------------------------------------------------------

def discover_agents(root: Path) -> dict[str, dict]:
    """Mapeia agentes → sessões JSONL e destino de output."""
    base = root / OPENCLAW_DIR / SESSIONS_DIR
    if not base.exists():
        return {}

    agents = {}
    for agent_dir in sorted(base.iterdir()):
        if not agent_dir.is_dir():
            continue
        sessions_dir = agent_dir / "sessions"
        if not sessions_dir.exists():
            continue

        name = agent_dir.name
        # Busca sessões ativas (.jsonl) e deletadas (.jsonl.deleted.*)
        files = sorted(list(sessions_dir.glob("*.jsonl")) + list(sessions_dir.glob("*.jsonl.deleted*")))

        # Destino: main respeita legado workspace/memory/ se existir
        if name == "main":
            legacy = root / OPENCLAW_DIR / "workspace" / "memory"
            output = legacy if legacy.exists() else root / OPENCLAW_DIR / "workspaces" / name / "memory"
        else:
            output = root / OPENCLAW_DIR / "workspaces" / name / "memory"

        agents[name] = {"files": files, "output": output}

    return agents
