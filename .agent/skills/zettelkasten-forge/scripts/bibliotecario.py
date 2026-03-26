"""
Zettelkasten Librarian — Auditor de Memória Ativa.
Detecta colisões entre notas atômicas dentro do active/ (cross-check entre categorias),
arquivando notas obsoletas/resolvidas no archive/ (pasta irmã de active/).
Agnóstico a caminhos: usa --active-dir ou lê da sessão salva pelo Destilador.
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

# Core Modules
from core.config import VALID_CATEGORIES
from core.llm_client import ask_llm
from core.zettel_io import extract_tags, get_file_content, obsidian_link
from core.session_paths import get_active_dir, get_archive_dir
from prompts.librarian_prompts import BIBLIOTECARIO_SYSTEM_PROMPT, BIBLIOTECARIO_USER_PROMPT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("librarian")


def get_librarian_decisions(new_note: dict, existing_notes: list[dict], dry_run: bool) -> dict:
    context_str = ""
    for note in existing_notes:
        content_trunc = note["content"][:2000]
        context_str += f"\n\n--- [NOTA ANTIGA] Arquivo: {note['filename']} ---\n{content_trunc}\n"

    prompt = BIBLIOTECARIO_USER_PROMPT.format(
        new_filename=new_note["filename"],
        new_content=new_note["content"][:3000],
        existing_context=context_str
    )

    if dry_run:
        logger.info("[DRY-RUN] Pulando consulta LLM para %d colisões.", len(existing_notes))
        return {"archived_notes": [], "related_notes": []}

    response = ask_llm(BIBLIOTECARIO_SYSTEM_PROMPT, prompt)
    return {
        "archived_notes": response.get("archived_notes", []),
        "related_notes": response.get("related_notes", [])
    }


def load_all_notes(directory: Path) -> list[dict]:
    """Carrega todas as notas atômicas de um diretório de categorias."""
    notes = []
    for cat in VALID_CATEGORIES:
        drawer = directory / cat
        if drawer.exists():
            for md_file in drawer.rglob("*.md"):
                content = get_file_content(md_file)
                notes.append({
                    "path": md_file,
                    "filename": md_file.name,
                    "category": md_file.parent.name,
                    "tags": extract_tags(content),
                    "content": content
                })
    return notes


def process_librarian_flow(active_dir: Path, archive_dir: Path, dry_run: bool):
    """
    Audita as notas atômicas dentro de active/, detecta colisões entre categorias
    (ex: pending vs decisions) e arquiva as que foram resolvidas/suplantadas.
    """
    if not active_dir.exists():
        logger.error("❌ active_dir não encontrado: %s", active_dir)
        return

    all_notes = load_all_notes(active_dir)
    logger.info("📚 %d notas atômicas carregadas de %s", len(all_notes), active_dir)

    if not all_notes:
        logger.info("📭 Nenhuma nota atômica encontrada. Encerrando.")
        return

    # Audita cada nota comparando-a com as demais (cross-check entre categorias)
    processed = set()
    for note in all_notes:
        if note["filename"] in processed:
            continue

        overlapping = [
            n for n in all_notes
            if n["filename"] != note["filename"]
            and note["tags"].intersection(n["tags"])
            and n["filename"] not in processed
        ]

        if not overlapping:
            continue

        logger.info("-" * 60)
        logger.info("Auditando: %s (%s)", note["filename"], note["category"])
        logger.info("  ├─ %d notas com tags sobrepostas: %s", len(overlapping), note["tags"])

        relations = get_librarian_decisions(
            {"filename": note["filename"], "content": note["content"]},
            overlapping,
            dry_run
        )

        if dry_run:
            archived = [a.get("filename") if isinstance(a, dict) else a for a in relations.get("archived_notes", [])]
            logger.info("[DRY-RUN] Arquivaria: %s", archived)
            continue

        # Arquivar notas obsoletas/resolvidas
        archived_notes_raw = relations.get("archived_notes", [])
        archived_notes = archived_notes_raw if isinstance(archived_notes_raw, list) else []
        for arch in archived_notes:
            arch_dict = arch if isinstance(arch, dict) else {}
            arch_filename = str(arch_dict.get("filename", ""))
            arch_reason = str(arch_dict.get("reason", "Substituído por nota mais recente."))

            note_data = next((n for n in overlapping if n["filename"] == arch_filename), None)
            if note_data:
                old_path = Path(str(note_data["path"]))
                hdr = (
                    f"> [!WARNING]\n> **Status:** 📦 ARQUIVADO / RESOLVIDO\n"
                    f"> **Motivo:** {arch_reason}\n"
                    f"> **Substituído por:** {obsidian_link(note['filename'])}\n\n"
                )
                archive_dest = archive_dir / str(note_data["category"]) / arch_filename
                archive_dest.parent.mkdir(parents=True, exist_ok=True)
                archive_dest.write_text(hdr + str(note_data["content"]), encoding="utf-8")
                old_path.unlink(missing_ok=True)
                logger.info("  > 📦 %s ARQUIVADO! Motivo: %s", arch_filename, arch_reason)
                processed.add(arch_filename)

        processed.add(note["filename"])

    logger.info("=" * 60)
    logger.info("✅ Auditoria concluída. Archive em: %s", archive_dir)


def main():
    parser = argparse.ArgumentParser(description="🧠 Zettelkasten Librarian — Auditor de Memória Ativa")
    parser.add_argument(
        "--active-dir", "-a", type=str, default=None,
        help="Pasta active/ com os átomos destilados. Se omitido, usa a sessão salva pelo Destilador."
    )
    parser.add_argument("--dry-run", action="store_true", help="Simula sem arquivar nada")
    args = parser.parse_args()

    active_dir = get_active_dir(fallback=args.active_dir)
    if not active_dir:
        logger.error("❌ Nenhum active_dir encontrado. Passe --active-dir ou rode o Destilador primeiro.")
        sys.exit(1)

    archive_dir = get_archive_dir(active_dir)
    logger.info("📂 active_dir : %s", active_dir)
    logger.info("📦 archive_dir: %s", archive_dir)

    process_librarian_flow(active_dir=active_dir, archive_dir=archive_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
