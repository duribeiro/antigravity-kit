#!/usr/bin/env python3
"""
analyze_clauses.py — Legal Document Clause Analyzer
Analisa documentos jurídicos e extrai cláusulas problemáticas.

Uso:
    python analyze_clauses.py --input <arquivo> [--output <saida.json>] [--lang pt]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

# ────────────────────────────────────────────────
# CONSTANTES
# ────────────────────────────────────────────────

VERSION = "1.0.0"

CLAUSE_PATTERNS: dict[str, list[str]] = {
    "penalidade_financeira": [
        r"multa\s+de\s+\d+", r"penalidade", r"indenização\s+de", r"cobrança\s+adicional",
        r"taxa\s+de\s+cancelamento", r"encargo\s+moratório", r"juros\s+de\s+mora",
        r"cláusula\s+penal", r"multa\s+rescisória",
    ],
    "renovacao_automatica": [
        r"renova.{0,20}automaticamente", r"prorrogação\s+tácita", r"prorrogação\s+automática",
        r"renovação\s+automática", r"findo\s+o\s+prazo.{0,50}renovar",
        r"sem\s+manifestação.{0,30}renovado",
    ],
    "coleta_de_dados": [
        r"dados\s+pessoais", r"informações\s+coletadas", r"compartilhamento\s+de\s+dados",
        r"terceiros\s+autorizados", r"finalidade.{0,30}dados", r"LGPD",
        r"cookies", r"rastreamento", r"dados\s+sensíveis", r"tratamento\s+de\s+dados",
    ],
    "rescisao_unilateral": [
        r"rescindir\s+sem\s+aviso", r"encerrar\s+a\s+qualquer\s+momento",
        r"suspender\s+unilateralmente", r"rescindir\s+imediatamente",
        r"direito\s+de\s+encerrar", r"término\s+imediato",
    ],
    "limitacao_de_direitos": [
        r"renuncia", r"isenta.{0,20}responsabilidade", r"não\s+pode\s+exigir",
        r"vedado\s+ao\s+usuário", r"não\s+será\s+responsável", r"excluída.{0,20}responsabilidade",
        r"sem\s+direito\s+a\s+indenização", r"assume\s+todo\s+o\s+risco",
    ],
    "foro_e_jurisdicao": [
        r"foro\s+eleito", r"arbitragem\s+obrigatória", r"comarca\s+de",
        r"jurisdiction", r"lei\s+aplicável", r"resolução\s+de\s+disputas",
        r"câmara\s+arbitral",
    ],
    "propriedade_intelectual": [
        r"cede\s+os\s+direitos", r"licença\s+irrevogável", r"conteúdo\s+gerado",
        r"propriedade\s+intelectual", r"direitos\s+autorais", r"transfere\s+os\s+direitos",
        r"uso\s+não\s+exclusivo", r"sublicenciar",
    ],
    "comunicacao_forcada": [
        r"aceita\s+receber", r"concorda\s+em\s+receber", r"notificações\s+automáticas",
        r"marketing\s+por\s+e-mail", r"comunicações\s+comerciais", r"opt-out",
    ],
}

SEVERITY_MAP: dict[str, str] = {
    "penalidade_financeira": "alta",
    "renovacao_automatica": "alta",
    "rescisao_unilateral": "alta",
    "limitacao_de_direitos": "alta",
    "coleta_de_dados": "media",
    "propriedade_intelectual": "media",
    "foro_e_jurisdicao": "media",
    "comunicacao_forcada": "baixa",
}

CATEGORY_LABELS: dict[str, str] = {
    "penalidade_financeira": "💰 Penalidade Financeira",
    "renovacao_automatica": "🔄 Renovação Automática",
    "coleta_de_dados": "🔒 Coleta de Dados",
    "rescisao_unilateral": "🚪 Rescisão Unilateral",
    "limitacao_de_direitos": "⛔ Limitação de Direitos",
    "foro_e_jurisdicao": "📌 Foro e Jurisdição",
    "propriedade_intelectual": "🔐 Propriedade Intelectual",
    "comunicacao_forcada": "📣 Comunicação Forçada",
}


# ────────────────────────────────────────────────
# FUNÇÕES CORE
# ────────────────────────────────────────────────

def load_document(path: str) -> str:
    """Carrega o documento de texto a partir do caminho informado."""
    file_path = Path(path)
    if not file_path.exists():
        print(f"[ERRO] Arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(1)
    return file_path.read_text(encoding="utf-8")


def split_into_paragraphs(text: str) -> list[str]:
    """Divide o documento em parágrafos para rastreamento de localização."""
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def analyze_document(text: str) -> list[dict]:
    """
    Analisa o documento e retorna lista de cláusulas problemáticas encontradas.
    
    Returns:
        Lista de dicts com: categoria, label, severidade, trecho, paragrafo_idx
    """
    paragraphs = split_into_paragraphs(text)
    findings: list[dict] = []

    for category, patterns in CLAUSE_PATTERNS.items():
        for idx, paragraph in enumerate(paragraphs):
            for pattern in patterns:
                matches = re.findall(pattern, paragraph, flags=re.IGNORECASE)
                if matches:
                    # Extrai contexto: 150 chars ao redor do match
                    match_obj = re.search(pattern, paragraph, re.IGNORECASE)
                    start = max(0, match_obj.start() - 80)
                    end = min(len(paragraph), match_obj.end() + 80)
                    excerpt = f"...{paragraph[start:end]}..."

                    findings.append({
                        "categoria": category,
                        "label": CATEGORY_LABELS[category],
                        "severidade": SEVERITY_MAP[category],
                        "trecho": excerpt.strip(),
                        "paragrafo_idx": idx + 1,
                        "gatilho": matches[0],
                    })
                    break  # Apenas 1 match por parágrafo por categoria

    return findings


def deduplicate_findings(findings: list[dict]) -> list[dict]:
    """Remove duplicatas mantendo o mais completo por categoria."""
    seen: set[str] = set()
    unique: list[dict] = []
    for item in findings:
        key = item["categoria"]
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def build_output(findings: list[dict], doc_path: str) -> dict:
    """Monta o JSON de saída estruturado."""
    return {
        "documento": doc_path,
        "total_clausulas_problematicas": len(findings),
        "clausulas": findings,
        "versao_analisador": VERSION,
    }


def print_summary(findings: list[dict]) -> None:
    """Exibe resumo no terminal."""
    print("\n" + "=" * 60)
    print("  ANÁLISE DE CLÁUSULAS PROBLEMÁTICAS")
    print("=" * 60)
    print(f"  Total encontrado: {len(findings)} cláusia(s) problemática(s)\n")

    for f in findings:
        severity_icon = {"alta": "🔴", "media": "🟡", "baixa": "🟢"}.get(f["severidade"], "⚪")
        print(f"  {severity_icon} {f['label']}")
        print(f"     Parágrafo #{f['paragrafo_idx']}")
        print(f"     \"{f['trecho'][:120]}...\"")
        print()
    print("=" * 60)


# ────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisa documentos jurídicos e extrai cláusulas problemáticas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python analyze_clauses.py --input contrato.txt
  python analyze_clauses.py --input termos.txt --output clausulas.json
  python analyze_clauses.py --input aluguel.txt --output result.json --quiet
        """,
    )
    parser.add_argument("--input", "-i", required=True, help="Caminho para o documento .txt")
    parser.add_argument("--output", "-o", help="Caminho para salvar o JSON de saída (opcional)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suprime saída no terminal")
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {VERSION}")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 1. Carrega documento
    text = load_document(args.input)

    # 2. Analisa
    findings = analyze_document(text)
    findings = deduplicate_findings(findings)

    # 3. Constrói saída
    output = build_output(findings, args.input)

    # 4. Exibe no terminal
    if not args.quiet:
        print_summary(findings)

    # 5. Salva JSON (opcional)
    if args.output:
        out_path = Path(args.output)
        out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\n✅ Resultado salvo em: {args.output}")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
