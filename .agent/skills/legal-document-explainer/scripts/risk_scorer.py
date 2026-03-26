#!/usr/bin/env python3
"""
risk_scorer.py — Legal Document Risk Scorer
Calcula o placar de risco de um documento jurídico com base nas cláusulas problemáticas.

Uso:
    python risk_scorer.py --clauses <clausulas.json>
    python risk_scorer.py --clauses <clausulas.json> --output risk_report.json
"""

import argparse
import json
import sys
from pathlib import Path

VERSION = "1.0.0"

# ────────────────────────────────────────────────
# PESOS POR SEVERIDADE
# ────────────────────────────────────────────────

SEVERITY_WEIGHTS: dict[str, int] = {
    "alta": 3,
    "media": 2,
    "baixa": 1,
}

# Limites de pontuação para classificação
RISK_THRESHOLDS = {
    "baixo": (0, 4),    # 0-4 pontos
    "medio": (5, 9),    # 5-9 pontos
    "alto": (10, 999),  # 10+
}

RISK_LABELS = {
    "baixo": "🟢 BAIXO",
    "medio": "🟡 MÉDIO",
    "alto": "🔴 ALTO",
}

RISK_DESCRIPTIONS = {
    "baixo": (
        "O documento apresenta poucos pontos de atenção e nenhuma cláusula "
        "considerada abusiva de forma grave. Leia com calma, tire suas dúvidas "
        "e assine com consciência."
    ),
    "medio": (
        "O documento contém cláusulas que merecem atenção especial antes da assinatura. "
        "Recomenda-se negociar ou esclarecer os pontos sinalizados com a outra parte."
    ),
    "alto": (
        "ATENÇÃO: Este documento apresenta múltiplas cláusulas potencialmente abusivas "
        "ou de alto impacto financeiro/legal. Consulte um advogado antes de assinar."
    ),
}


# ────────────────────────────────────────────────
# LÓGICA CORE
# ────────────────────────────────────────────────

def load_clauses(path: str) -> dict:
    """Carrega o JSON de cláusulas gerado pelo analyze_clauses.py."""
    file_path = Path(path)
    if not file_path.exists():
        print(f"[ERRO] Arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(file_path.read_text(encoding="utf-8"))


def calculate_score(clauses: list[dict]) -> tuple[int, str]:
    """
    Calcula pontuação de risco.

    Returns:
        Tupla (pontuação_total, nivel_risco)
    """
    total = sum(SEVERITY_WEIGHTS.get(c.get("severidade", "baixa"), 1) for c in clauses)
    
    nivel = "baixo"
    for key, (low, high) in RISK_THRESHOLDS.items():
        if low <= total <= high:
            nivel = key
            break
    
    return total, nivel


def build_breakdown(clauses: list[dict]) -> list[dict]:
    """Gera o detalhamento da pontuação por categoria."""
    return [
        {
            "categoria": c["label"],
            "severidade": c["severidade"],
            "pontos": SEVERITY_WEIGHTS.get(c["severidade"], 1),
        }
        for c in clauses
    ]


def print_risk_report(score: int, nivel: str, breakdown: list[dict], doc: str) -> None:
    """Imprime o relatório de risco no terminal."""
    border = "═" * 50
    print(f"\n╔{border}╗")
    print(f"║{'PLACAR DE RISCO DO DOCUMENTO':^50}║")
    print(f"╠{border}╣")
    print(f"║  Documento: {Path(doc).name:<38}║")
    print(f"║  Pontuação: {score:<38}║")
    print(f"║  Nível:     {RISK_LABELS[nivel]:<35}║")
    print(f"╠{border}╣")
    print(f"║  {'Justificativa:':<49}║")

    desc = RISK_DESCRIPTIONS[nivel]
    words = desc.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 > 46:
            print(f"║  {line:<48}║")
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        print(f"║  {line:<48}║")

    print(f"╠{border}╣")
    print(f"║  {'Detalhamento por cláusula:':<49}║")
    for item in breakdown:
        row = f"  • {item['categoria'][:35]} [{item['pontos']}pt]"
        print(f"║{row:<50}║")
    print(f"╚{border}╝\n")


# ────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calcula o placar de risco de um documento jurídico.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python risk_scorer.py --clauses clausulas.json
  python risk_scorer.py --clauses clausulas.json --output risco.json
        """,
    )
    parser.add_argument("--clauses", "-c", required=True, help="JSON gerado pelo analyze_clauses.py")
    parser.add_argument("--output", "-o", help="Caminho para salvar resultado JSON (opcional)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suprime saída no terminal")
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {VERSION}")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    data = load_clauses(args.clauses)
    clauses = data.get("clausulas", [])
    doc = data.get("documento", "desconhecido")

    score, nivel = calculate_score(clauses)
    breakdown = build_breakdown(clauses)

    if not args.quiet:
        print_risk_report(score, nivel, breakdown, doc)

    result = {
        "documento": doc,
        "pontuacao": score,
        "nivel_risco": nivel,
        "label_risco": RISK_LABELS[nivel],
        "descricao": RISK_DESCRIPTIONS[nivel],
        "detalhamento": breakdown,
        "versao_scorer": VERSION,
    }

    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"✅ Risco salvo em: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
