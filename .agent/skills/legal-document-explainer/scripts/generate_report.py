#!/usr/bin/env python3
"""
generate_report.py — Legal Document Report Generator
Gera um relatório completo em Markdown a partir da análise de cláusulas e risco.

Uso:
    python generate_report.py --clauses <clausulas.json> [--risk <risco.json>] --output relatorio.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

VERSION = "1.0.0"

QUESTION_TEMPLATES: dict[str, list[str]] = {
    "penalidade_financeira": [
        "Qual é o valor exato da multa em caso de cancelamento antecipado?",
        "Existe alguma forma de reduzir ou isentar a multa nos primeiros dias?",
        "A multa é proporcional ao tempo restante do contrato?",
    ],
    "renovacao_automatica": [
        "Com quanto tempo de antecedência devo comunicar o cancelamento para evitar a renovação?",
        "Existe algum canal formal para comunicar a não-renovação?",
        "O contrato pode ser renovado por prazo menor do que o original?",
    ],
    "coleta_de_dados": [
        "Quais dados pessoais exatamente serão coletados?",
        "Com quais terceiros meus dados podem ser compartilhados?",
        "Como posso solicitar a exclusão dos meus dados (direito ao esquecimento - LGPD)?",
    ],
    "rescisao_unilateral": [
        "Em quais situações a outra parte pode rescindir o contrato sem aviso?",
        "Terei direito a alguma indenização em caso de rescisão unilateral?",
        "Qual é o aviso prévio mínimo para rescisão?",
    ],
    "limitacao_de_direitos": [
        "Esta cláusula de limitação de responsabilidade é negociável?",
        "Em caso de dano causado pela outra parte, quais recursos ainda tenho disponíveis?",
    ],
    "foro_e_jurisdicao": [
        "Por que o foro eleito é diferente da minha cidade?",
        "Existe previsão de arbitragem e qual é o custo médio do procedimento?",
        "Posso negociar a mudança do foro para a minha comarca?",
    ],
    "propriedade_intelectual": [
        "Que tipo de conteúdo é considerado transferido para a plataforma?",
        "Posso continuar usando meu próprio conteúdo fora da plataforma?",
        "A licença concedida expira se eu encerrar minha conta?",
    ],
    "comunicacao_forcada": [
        "Como faço para cancelar o recebimento de comunicações de marketing?",
        "As comunicações obrigatórias são apenas sobre o contrato ou incluem publicidade?",
    ],
}

UNIVERSAL_QUESTIONS = [
    "Posso solicitar alterações em alguma cláusula antes de assinar?",
    "Qual é o prazo para reflexão (arrependimento) após a assinatura?",
    "Existe versão atualizada deste documento? Quando foi a última revisão?",
    "Em caso de dúvida futura, a qual departamento/contato devo recorrer?",
]


def load_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"[ERRO] Arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(p.read_text(encoding="utf-8"))


def get_risk_emoji(nivel: str) -> str:
    return {"baixo": "🟢", "medio": "🟡", "alto": "🔴"}.get(nivel, "⚪")


def build_questions(clauses: list[dict]) -> list[str]:
    """Monta lista de perguntas com base nas categorias encontradas."""
    questions = list(UNIVERSAL_QUESTIONS)
    for clause in clauses:
        category = clause.get("categoria", "")
        specific = QUESTION_TEMPLATES.get(category, [])
        for q in specific:
            if q not in questions:
                questions.append(q)
    return questions


def generate_markdown(clauses_data: dict, risk_data: dict | None) -> str:
    """Gera o relatório completo em Markdown."""
    doc = clauses_data.get("documento", "documento-não-identificado")
    clauses = clauses_data.get("clausulas", [])
    now = datetime.now().strftime("%d/%m/%Y às %H:%M")

    nivel = risk_data.get("nivel_risco", "desconhecido") if risk_data else "não calculado"
    score = risk_data.get("pontuacao", "-") if risk_data else "-"
    risk_emoji = get_risk_emoji(nivel) if risk_data else "⚪"
    risk_desc = risk_data.get("descricao", "") if risk_data else ""

    lines: list[str] = []

    # Cabeçalho
    lines += [
        "# ⚖️ Relatório de Análise Jurídica",
        "",
        f"> **Documento:** `{Path(doc).name}`  ",
        f"> **Gerado em:** {now}  ",
        f"> **Placar de Risco:** {risk_emoji} **{nivel.upper()}** ({score} pontos)",
        "",
        "---",
        "",
        "> ⚠️ **Aviso Legal:** Este relatório é informativo e não substitui aconselhamento jurídico profissional.",
        "",
        "---",
        "",
    ]

    # Placar de Risco
    lines += [
        "## 🎯 Placar de Risco",
        "",
        f"| Nível | Pontuação | Avaliação |",
        f"|-------|-----------|-----------|",
        f"| {risk_emoji} {nivel.upper()} | {score} pontos | {risk_desc[:80]}... |" if risk_desc else f"| {risk_emoji} {nivel.upper()} | {score} pontos | — |",
        "",
        "---",
        "",
    ]

    # Cláusulas Problemáticas
    lines += [
        "## 🚨 Cláusulas Problemáticas Identificadas",
        "",
        f"**Total encontrado:** {len(clauses)} cláusula(s)",
        "",
    ]

    if not clauses:
        lines.append("✅ Nenhuma cláusula problemática identificada automaticamente. Recomenda-se leitura integral.")
    else:
        for i, clause in enumerate(clauses, 1):
            sev = clause.get("severidade", "baixa")
            sev_icon = {"alta": "🔴", "media": "🟡", "baixa": "🟢"}.get(sev, "⚪")
            lines += [
                f"### {i}. {clause.get('label', 'Cláusula')} {sev_icon}",
                "",
                f"- **Localização:** Parágrafo #{clause.get('paragrafo_idx', '?')}",
                f"- **Severidade:** {sev_icon} {sev.upper()}",
                f"- **Gatilho detectado:** `{clause.get('gatilho', '?')}`",
                "",
                f"> 📖 **Trecho:** _{clause.get('trecho', '')}_",
                "",
            ]

    lines += ["---", ""]

    # Perguntas Práticas
    questions = build_questions(clauses)
    lines += [
        "## ❓ Perguntas Práticas Antes de Assinar",
        "",
        "_Faça estas perguntas à outra parte ou ao seu advogado antes de assinar:_",
        "",
    ]

    for i, q in enumerate(questions, 1):
        lines.append(f"{i}. {q}")

    lines += ["", "---", ""]

    # Tabela de Status Rápido  
    lines += [
        "## 📊 Tabela de Status",
        "",
        "| Aspecto | Status | Encontrado |",
        "|---------|--------|------------|",
    ]

    categorias_status = {
        "penalidade_financeira": ("💰 Multa/Penalidade", "⚠️"),
        "renovacao_automatica": ("🔄 Renovação Auto", "⚠️"),
        "coleta_de_dados": ("🔒 Coleta de Dados", "⚠️"),
        "rescisao_unilateral": ("🚪 Rescisão Unilateral", "⚠️"),
        "limitacao_de_direitos": ("⛔ Limitação de Direitos", "⚠️"),
        "foro_e_jurisdicao": ("📌 Foro/Arbitragem", "⚠️"),
        "propriedade_intelectual": ("🔐 Propriedade Intelectual", "⚠️"),
        "comunicacao_forcada": ("📣 Comunicação Forçada", "⚠️"),
    }

    found_categories = {c["categoria"] for c in clauses}

    for cat_key, (label, warn) in categorias_status.items():
        if cat_key in found_categories:
            lines.append(f"| {label} | {warn} Detectado | Sim |")
        else:
            lines.append(f"| {label} | ✅ Não detectado | Não |")

    lines += [
        "",
        "---",
        "",
        "_Este relatório foi gerado automaticamente pela skill **legal-document-explainer** v1.0.0._",
    ]

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera relatório completo em Markdown a partir da análise jurídica.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python generate_report.py --clauses clausulas.json --output relatorio.md
  python generate_report.py --clauses clausulas.json --risk risco.json --output relatorio.md
        """,
    )
    parser.add_argument("--clauses", "-c", required=True, help="JSON de cláusulas (analyze_clauses.py)")
    parser.add_argument("--risk", "-r", help="JSON de risco (risk_scorer.py) — opcional")
    parser.add_argument("--output", "-o", required=True, help="Caminho do relatório .md de saída")
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {VERSION}")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    clauses_data = load_json(args.clauses)
    risk_data = load_json(args.risk) if args.risk else None

    markdown = generate_markdown(clauses_data, risk_data)

    out_path = Path(args.output)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"✅ Relatório gerado em: {args.output}")


if __name__ == "__main__":
    main()
