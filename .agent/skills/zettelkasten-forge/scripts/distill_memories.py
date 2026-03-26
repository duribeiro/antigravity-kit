"""
Atomic Memory Distillation Pipeline (CLI Entrypoint).
SRP: CLI routing, reading input files, and delegating to core modules.
"""
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add scripts directory to sys.path so it works from anywhere
sys.path.append(str(Path(__file__).resolve().parent))

# Core Modules
from core.config import VALID_CATEGORIES
from core.text_cleaner import clean_text
from core.llm_client import ask_llm
from core.zettel_io import get_file_content, slugify
from core.session_paths import save_session
from prompts.distill_prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("distiller")

def extract_session_date(filename: str) -> str:
    parts = filename.split("_")
    if len(parts) >= 2 and len(parts[0]) == 10:
        return f"{parts[0]}_{parts[1]}"
    return datetime.now().strftime("%Y-%m-%d_%H-%M")

def extract_insights(cleaned_text: str, filename: str, date: str, dry_run: bool) -> list[dict]:
    prompt = USER_PROMPT_TEMPLATE.format(
        source_filename=filename,
        session_date=date,
        cleaned_content=cleaned_text[:100000]
    )
    if dry_run:
        logger.info("[DRY-RUN] Insight Extractor invocado com sucesso (%d chars).", len(prompt))
        return []
    
    response = ask_llm(SYSTEM_PROMPT, prompt)
    atoms = response.get("atoms", [])
    for atom in atoms:
        if atom.get("category") not in VALID_CATEGORIES:
            atom["category"] = "triage"
    return atoms

def save_atoms(atoms: list[dict], filename: str, date: str, output_dir: Path, dry_run: bool) -> int:
    """Salva átomos destilados no output_dir. As categorias são criadas como subpastas."""
    saved = 0
    for i, atom in enumerate(atoms, 1):
        category = atom.get("category", "triage")
        title = atom.get("title", f"atom_{i}")
        tags = atom.get("tags", [])
        content = atom.get("content", "")
        quotes = atom.get("impact_quotes", [])

        slug = slugify(title)
        out_name = f"{date}_{slug}.md"
        out_path = output_dir / category / out_name

        tags_line = " ".join(tags)
        quotes_section = "\n".join(f'> "{q}"' for q in quotes) if quotes else ""
        if quotes_section:
             quotes_section = f"\n\n### Citações de Impacto\n{quotes_section}"

        md_content = (
            f"# {title}\n"
            f"Tags: {tags_line}\n\n---\n\n"
            f"{content}{quotes_section}\n\n"
            f"---\n*Fonte: {filename}*\n"
        )

        if dry_run:
             logger.info("[DRY-RUN] Átomo gerado: %s/%s", category, out_name)
             continue

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_content, encoding="utf-8")
        saved += 1
        logger.info("✅ Salvo: %s/%s", category, out_name)
    return saved

def process_file(filepath: Path, output_dir: Path, dry_run: bool) -> dict:
    logger.info("=" * 60)
    logger.info("Processando: %s", filepath.name)

    raw_text = get_file_content(filepath)
    raw_size = len(raw_text)

    cleaned_text, stats = clean_text(raw_text)
    clean_size = len(cleaned_text)
    logger.info("🪓 TextCleaner reduziu ruído: %d -> %d bytes", raw_size, clean_size)

    if clean_size < 100:
        logger.warning("⏭️ Arquivo muito pequeno (%d). Pulando LLM Extractor.", clean_size)
        return {"file": filepath.name, "raw": raw_size, "clean": clean_size, "atoms": 0}

    date = extract_session_date(filepath.name)
    logger.info("🔥 Ativando Insight Extractor (LLM)...")
    atoms = extract_insights(cleaned_text, filepath.name, date, dry_run)
    saved = save_atoms(atoms, filepath.name, date, output_dir, dry_run)

    return {"file": filepath.name, "raw": raw_size, "clean": clean_size, "atoms": saved}

def main():
    parser = argparse.ArgumentParser(description="🧠 Memory Distiller (Modularized)")
    parser.add_argument("--input", "-i", type=str, help="Arquivo .md único para destilar")
    parser.add_argument("--input-dir", "-d", type=str, help="Pasta com arquivos .md brutos")
    parser.add_argument("--output-dir", "-o", type=str, required=True,
                        help="Pasta de destino dos átomos destilados (ex: .../active)")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem escrever nada")
    parser.add_argument("--clean-only", action="store_true", help="Apenas limpa e exibe o texto")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    files = []

    if args.input:
        p = Path(args.input).resolve()
        if p.exists():
            files.append(p)
        else:
            logger.error("Arquivo não encontrado: %s", args.input)
            sys.exit(1)

    if args.input_dir:
        d = Path(args.input_dir).resolve()
        files.extend(sorted(d.glob("*.md")))

    if not files:
        logger.warning("Nenhum arquivo encontrado.")
        sys.exit(0)

    # Salva sessão para que o Bibliotecário saiba onde buscar depois
    if not args.dry_run:
        input_ref = args.input_dir or args.input or ""
        save_session(input_dir=input_ref, active_dir=str(output_dir))
        logger.info("📍 Sessão salva. Bibliotecário pode usar automaticamente o output_dir.")

    for f in files:
        if args.clean_only:
            logger.info("🧹 CLEAN-ONLY RESULTS: %s", f.name)
            cleaned, _ = clean_text(get_file_content(f))
            print(f"\n{cleaned[:2000]}{'...' if len(cleaned) > 2000 else ''}")
            continue
        process_file(f, output_dir, args.dry_run)

if __name__ == "__main__":
    main()
