---
name: zettelkasten-forge
description: Processa, destila e consolida memória bruta em Átomos de Conhecimento organizados em categorias semânticas (decisions, lessons, pending, people, projects). Agnóstico a caminhos — origem e destino são sempre passados como parâmetros. Acionado via comando ou rotina diária.
---

# Zettelkasten Forge

> **Esta skill transforma logs brutos em regras e aprendizados imutáveis de longo prazo (Átomos Zettelkasten), descentralizados em pastas semânticas.**

## 🚀 Quando e Como Usar

Acione esta skill quando o usuário disser "consolide as memórias", "rode o Zettelkasten" ou fornecer um diretório de logs brutos para destilação.

## 🏗 Arquitetura

```
scripts/
├── distill_memories.py  ← CLI: Extrai átomos dos logs brutos
├── bibliotecario.py     ← CLI: Audita e arquiva duplicatas/resolvidos
├── core/
│   ├── config.py        ← Constantes, categorias, modelos
│   ├── llm_client.py    ← Fallback LLM: Groq → Nvidia → Gemini
│   ├── text_cleaner.py  ← Remove ruído dos logs brutos
│   ├── zettel_io.py     ← I/O de arquivos Markdown
│   └── session_paths.py ← Persiste caminhos entre scripts (/tmp)
└── prompts/
    ├── distill_prompts.py   ← Prompt do Destilador
    └── librarian_prompts.py ← Prompt do Bibliotecário
```

## 🔄 Fluxo de Execução (2 Passos)

### Passo 1 — Destilador (Extrator de Átomos)

Lê logs brutos `.md` e grava átomos categorizados no `<OUTPUT_DIR>`.
Ao terminar, salva automaticamente o caminho em `/tmp/forge_session.json`.

```bash
python <SKILL_DIR>/scripts/distill_memories.py \
  --input-dir "<PASTA_COM_LOGS_BRUTOS>" \
  --output-dir "<PASTA_ACTIVE_DESTINO>"
```

- `--input-dir`: Pasta contendo os arquivos `.md` brutos (ex: `.../staging`)
- `--output-dir`: Pasta onde os átomos serão criados em subcategorias (ex: `.../active`)
- `--dry-run`: Simula sem gravar nada

### Passo 2 — Bibliotecário (Auditor de Memória Ativa)

Lê os átomos do `--active-dir`, detecta colisões por tags entre categorias e arquiva o que for obsoleto ou resolvido em `archive/` (pasta irmã de `active/`).

```bash
# Opção A: Automático (usa sessão salva pelo Destilador)
python <SKILL_DIR>/scripts/bibliotecario.py

# Opção B: Manual (quando rodar em sessões separadas)
python <SKILL_DIR>/scripts/bibliotecario.py \
  --active-dir "<PASTA_ACTIVE_DESTINO>"
```

- O `archive/` é sempre criado como **pasta irmã** do `--active-dir`
- `--dry-run`: Simula sem arquivar nada

## 📁 Estrutura de Diretórios Esperada

```
<BASE_MEMORY_DIR>/
├── staging/      ← Logs brutos (.md) — INPUT do Destilador
├── active/       ← Átomos destilados por categoria — OUTPUT do Destilador / INPUT do Bibliotecário
│   ├── decisions/
│   ├── lessons/
│   ├── pending/
│   ├── people/
│   └── projects/
└── archive/      ← Notas arquivadas/resolvidas — OUTPUT do Bibliotecário (criado automaticamente)
    ├── decisions/
    └── pending/
```

## Regras de Sobrevivência (MANDATORY)

1. **Agnóstico a Caminhos:** Sempre passe `--input-dir` e `--output-dir` explicitamente. Nunca assuma caminhos hardcoded.
2. **Memórias Descentralizadas:** Os átomos categorizados nas subpastas de `active/` são os artefatos finais. **Nunca force a consolidação em um arquivo `memory.md` único.**
3. **Pré-requisito:** Esta skill processa apenas `.md`. A conversão de `.jsonl` bruto para `.md` é responsabilidade do script `memory-miner` (skill separada).
4. **API Keys:** Inject via `.env` antes de rodar — nunca hardcode. Usar `GROQ_API_KEY`, `NVIDIA_API_KEY`, `GEMINI_API_KEY`.
