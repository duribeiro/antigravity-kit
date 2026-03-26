---
name: legal-document-explainer
description: Analisa e explica documentos jurídicos em linguagem simples (contratos, termos de serviço, contratos de aluguel, políticas de privacidade, etc.). Identifica cláusulas problemáticas como multas, renovação automática e coleta de dados, atribui um placar de risco (Baixo, Médio ou Alto) e sugere perguntas práticas que o usuário deveria fazer antes de assinar. Use quando o usuário enviar qualquer documento legal para análise, revisão ou explicação.
---

# Legal Document Explainer

Esta skill transforma documentos jurídicos complexos em linguagem clara e acessível. Ela identifica riscos, destaca cláusulas problemáticas e orienta o usuário com perguntas práticas antes de qualquer assinatura.

> ⚖️ **Aviso Legal:** Esta skill oferece análise informativa para fins educacionais. Não substitui aconselhamento jurídico profissional. Para decisões de alto impacto, sempre consulte um advogado.

---

## Quando Usar Esta Skill

- Usuário envia um contrato (aluguel, serviço, emprego, prestação, etc.)
- Usuário envia termos de serviço de um aplicativo ou plataforma
- Usuário envia política de privacidade para revisão
- Usuário quer entender o que está assinando
- Usuário pede para "explicar esse documento", "o que significa isso?", "tem algum risco?"
- Usuário menciona palavras-chave: "contrato", "termos", "assinar", "cláusula", "jurídico", "legal"

---

## Estrutura de Análise Obrigatória

Ao receber um documento jurídico, **SEMPRE** siga esta ordem de entrega:

### 📋 Passo 1 — Identificação do Documento

Identifique e declare:
- **Tipo de documento** (ex.: Contrato de Aluguel Residencial)
- **Partes envolvidas** (ex.: Locador X / Locatário Y)
- **Vigência / Prazo** (ex.: 12 meses, a partir de 01/04/2025)
- **Jurisdição** (ex.: Lei brasileira, LGPD, Código Civil)

---

### 📝 Passo 2 — Resumo Executivo (Linguagem Simples)

Escreva um resumo em **3 a 5 parágrafos curtos**, em linguagem acessível para qualquer pessoa. Use:
- Frases curtas (máximo 20 palavras)
- Sem jargão jurídico
- Analogias do cotidiano quando útil

---

### 🚨 Passo 3 — Mapeamento de Cláusulas Problemáticas

Use o script `analyze_clauses.py` para detectar automaticamente, ou faça manualmente seguindo o `assets/clause-patterns.json`.

Para cada cláusula problemática encontrada, entregue:

```
⚠️ [NOME DA CLÁUSULA]
📍 Localização: [Seção / Página / Parágrafo]
📖 Texto original: "[trecho literal do documento]"
💬 O que significa: [explicação em linguagem simples]
🎯 Por que é problemático: [impacto real para o usuário]
```

**Categorias de Cláusulas Monitoradas:**

| Categoria              | Exemplos de Gatilhos                                      |
|------------------------|-----------------------------------------------------------|
| 💰 Penalidades Financeiras | multa, penalidade, indenização, cobrança extra         |
| 🔄 Renovação Automática    | renova automaticamente, prorrogação tácita             |
| 🔒 Coleta de Dados         | dados pessoais, compartilhamento, terceiros, LGPD      |
| 🚪 Rescisão Unilateral     | rescindir sem aviso, encerrar a qualquer momento       |
| ⛔ Limitação de Direitos   | renuncia, isenta de responsabilidade, não pode exigir  |
| 📌 Foro e Jurisdição       | foro eleito, arbitragem obrigatória, comarca X         |
| 🔐 Propriedade Intelectual | conteúdo gerado, cede direitos, licença irrevogável    |
| 📣 Comunicação Forçada     | aceita receber, marketing, notificações automáticas    |

---

### 🎯 Passo 4 — Placar de Risco

Calcule o placar usando o script `risk_scorer.py` ou aplique manualmente a lógica do `assets/risk-rubric.md`.

**Exiba o resultado assim:**

```
╔══════════════════════════════╗
║  PLACAR DE RISCO DO DOCUMENTO ║
╠══════════════════════════════╣
║  🟢 Baixo    🟡 Médio   🔴 Alto ║
║                   [ ATUAL ]    ║
╠══════════════════════════════╣
║  Justificativa:               ║
║  [2-3 frases explicando]      ║
╚══════════════════════════════╝
```

**Critérios de Classificação:**

| Nível  | Critério                                                                 |
|--------|--------------------------------------------------------------------------|
| 🟢 Baixo  | ≤ 2 cláusulas problemáticas, sem penalidades financeiras severas        |
| 🟡 Médio  | 3-5 cláusulas problemáticas OU penalidades financeiras moderadas         |
| 🔴 Alto   | 6+ cláusulas OU cláusulas abusivas (direitos renunciados, multas altas)  |

---

### ❓ Passo 5 — Perguntas Práticas Antes de Assinar

Gere **5 a 10 perguntas** contextualizadas para o documento analisado. Divida-as em categorias:

**Perguntas Gerais (sempre incluir):**
- "Posso cancelar a qualquer momento sem multa? Após quanto tempo?"
- "Como serei notificado sobre mudanças nestas condições?"
- "Existe período de carência ou teste gratuito?"

**Perguntas Específicas por Tipo de Documento:**
- Use o template em `assets/question-templates.md` como base
- Personalize com os dados reais do documento analisado

---

### 📊 Passo 6 — Tabela de Resumo Final

Encerre com uma tabela de status rápido:

```markdown
| Aspecto                   | Status         | Detalhes                  |
|---------------------------|----------------|---------------------------|
| Prazo / Vigência          | ✅ / ⚠️ / 🔴  | [info]                    |
| Multa por Rescisão        | ✅ / ⚠️ / 🔴  | [info]                    |
| Renovação Automática      | ✅ / ⚠️ / 🔴  | [info]                    |
| Coleta de Dados Pessoais  | ✅ / ⚠️ / 🔴  | [info]                    |
| Limitação de Direitos     | ✅ / ⚠️ / 🔴  | [info]                    |
| Foro / Arbitragem         | ✅ / ⚠️ / 🔴  | [info]                    |
```

---

## Usando os Scripts Helper

Execute com `--help` primeiro para ver todas as opções disponíveis:

```bash
python scripts/analyze_clauses.py --help
python scripts/risk_scorer.py --help
python scripts/generate_report.py --help
```

**Fluxo recomendado:**
```bash
# 1. Analisa o documento e extrai cláusulas
python scripts/analyze_clauses.py --input documento.txt --output clauses.json

# 2. Calcula o placar de risco
python scripts/risk_scorer.py --clauses clauses.json

# 3. Gera relatório completo em Markdown
python scripts/generate_report.py --clauses clauses.json --output relatorio.md
```

---

## Decision Tree — Tipo de Documento

```
Documento recebido
       │
       ├─ É um CONTRATO DE ALUGUEL?
       │   └─ Foco: multas, prazo, vistoria, reajuste, rescisão
       │
       ├─ São TERMOS DE SERVIÇO / USO?
       │   └─ Foco: coleta de dados, rescisão unilateral, PI, foro
       │
       ├─ É POLÍTICA DE PRIVACIDADE?
       │   └─ Foco: LGPD, dados sensíveis, compartilhamento, retenção
       │
       ├─ É CONTRATO DE TRABALHO / PRESTAÇÃO?
       │   └─ Foco: jornada, não-concorrência, rescisão, benefícios
       │
       └─ Outro documento jurídico?
           └─ Aplica análise genérica + perguntas universais
```

---

## Formato de Saída Padrão

Sempre entregue a análise em formato **Markdown estruturado** com:
- Emojis para escaneabilidade visual
- Seções claramente separadas com `---`
- Tabelas para comparações rápidas
- Destaque `> ⚠️` para alertas críticos
- Linguagem em PT-BR

---

## Boas Práticas

- **Nunca minimize riscos**: Se houver dúvida, classifique para cima (Médio → Alto)
- **Cite sempre o trecho original**: O usuário precisa localizar a cláusula no documento
- **Seja empático**: O usuário provavelmente está confuso — use tom acolhedor
- **Não dê conselho jurídico definitivo**: Sempre sugira consultar um advogado para decisões críticas
- **Valide o contexto**: Pergunte a lei aplicável (Brasil, Portugal, etc.) se não estiver claro

---

## Referências

Consulte os arquivos em `references/` para embasamento técnico:
- `references/lgpd-key-articles.md` — Artigos da LGPD relevantes para análise
- `references/codigo-civil-referencias.md` — Artigos do Código Civil brasileiro
- `references/common-abusive-clauses.md` — Banco de cláusulas abusivas reconhecidas pelo Procon/CDC
