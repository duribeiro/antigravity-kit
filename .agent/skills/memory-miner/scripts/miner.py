"""
Memory Miner — CLI entry point.

Extração estruturada de sessões OpenClaw para Markdown.
Zero dependências externas. Zero chamadas de API. Zero tokens.

Uso:
    python miner.py <raiz> [--agent NOME] [--full] [--dry-run] [--list]
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from formatter import make_filename, make_slug, render_markdown, write_note
from parser import parse_session
from state import discover_agents, load_state, save_state


# ---------------------------------------------------------------------------
# Comandos CLI
# ---------------------------------------------------------------------------

def cmd_list(root: Path) -> None:
    """Lista todos os agentes e suas sessões."""
    agents = discover_agents(root)
    if not agents:
        print(f"Nenhum agente encontrado em {root}")
        return
    print(f"Agentes em {root}:\n")
    for name, info in agents.items():
        count = len(info["files"])
        marker = "✓" if count else "○"
        print(f"  {marker} {name:25s} ({count:3d} sessões) → {info['output']}")


def cmd_dry_run(root: Path, agent_filter: Optional[str]) -> None:
    """Preview do que será processado, sem escrever nada."""
    agents = discover_agents(root)
    processed = load_state(root)
    total = 0
    for name, info in agents.items():
        if agent_filter and name != agent_filter:
            continue
        pending = [f for f in info["files"] if str(f) not in processed]
        if not pending:
            print(f"  ○ {name}: nada novo")
            continue
        print(f"  ✓ {name}: {len(pending)} sessões → {info['output']}")
        for f in pending[:5]:
            print(f"    - {f.name} ({f.stat().st_size / 1024:.0f} KB)")
        if len(pending) > 5:
            print(f"    ... +{len(pending) - 5} mais")
        total += len(pending)
    print(f"\nTotal: {total} sessões. Custo: 0 tokens.")


def cmd_mine(root: Path, agent_filter: Optional[str], full: bool, out_dir: Optional[Path] = None) -> None:
    """Extrai sessões e salva notas agrupadas por hora."""
    agents = discover_agents(root)
    processed = set() if full else load_state(root)

    if full:
        print("🔄 Modo FULL ativado.\n")

    extracted = 0

    for name, info in agents.items():
        if agent_filter and name != agent_filter:
            continue

        pending = [f for f in info["files"] if str(f) not in processed]
        if not pending:
            print(f"  ○ {name}: nada novo")
            continue

        print(f"\n🔨 {name}: {len(pending)} sessões")

        # Buffer de agrupamento por hora: "YYYY-MM-DD-HH" -> [(content, filename)]
        hourly_buffer: dict[str, list[tuple[str, str]]] = {}

        for jsonl in pending:
            print(f"  → {jsonl.name}", end=" ", flush=True)

            try:
                session = parse_session(jsonl)
            except Exception as exc:
                print(f"⚠ erro: {exc}")
                continue

            if session.is_empty:
                print("⊘ (vazia)")
                processed.add(str(jsonl))
                continue

            content = render_markdown(session, session_id=jsonl.stem)
            slug = make_slug(session)
            filename = make_filename(session, slug)

            # Chave de agrupamento: YYYY-MM-DD-HH
            hour_key = session.first_ts[:13]
            hourly_buffer.setdefault(hour_key, []).append((content, filename))

            print(f"✓ ({hour_key}h)")
            processed.add(str(jsonl))

        # Salva o buffer agrupado por hora
        output_path = out_dir if out_dir else info["output"]
        for hour_key, items in hourly_buffer.items():
            base_filename = items[0][1]

            if len(items) == 1:
                note = write_note(items[0][0], base_filename, output_path)
                print(f"  📄 [{hour_key}h]: {note.name}")
            else:
                combined = "\n\n---\n\n".join(i[0] for i in items)
                note = write_note(combined, base_filename, output_path)
                print(f"  📦 [{hour_key}h]: {len(items)} sessões → {note.name}")
            extracted += 1

    save_state(root, processed)
    print(f"\n✓ Concluído: {extracted} notas geradas.")


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Memory Miner — Extração local de sessões OpenClaw para Markdown."
    )
    parser.add_argument("root", help="Raiz do agente OpenClaw")
    parser.add_argument("--list", action="store_true", help="Listar agentes disponíveis")
    parser.add_argument("--dry-run", action="store_true", help="Preview sem processar")
    parser.add_argument("--full", action="store_true", help="Reprocessar tudo (ignora estado delta)")
    parser.add_argument("--agent", metavar="NOME", help="Restringir a um agente específico")
    parser.add_argument("--out-dir", metavar="DIR", help="Forçar diretório de saída")

    args = parser.parse_args()
    root = Path(args.root)
    out_dir = Path(args.out_dir) if args.out_dir else None

    if not (root / ".openclaw").exists():
        print(f"✗ Diretório OpenClaw não encontrado: {root / '.openclaw'}")
        sys.exit(1)

    if args.list:
        cmd_list(root)
    elif args.dry_run:
        cmd_dry_run(root, args.agent)
    else:
        cmd_mine(root, args.agent, args.full, out_dir)


if __name__ == "__main__":
    main()
