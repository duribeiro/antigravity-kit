---
name: memory-miner
description: Extrai sessões JSONL de agentes OpenClaw em notas Markdown preservando 100% das palavras originais, timestamps e canal de comunicação. Zero tokens, zero dependências externas.
---

# Memory Miner

Garimpeiro de memórias: lê sessões JSONL brutas de agentes OpenClaw e gera notas Raw-First com palavras originais preservadas.

## Características

- **100% offline** — zero chamadas de API, zero tokens consumidos
- **Preservação total** — mensagens originais do usuário e do agente, sem curadoria
- **Timestamps precisos** — cada mensagem mantém seu horário real
- **Canal detectado** — Discord, WhatsApp, Cron ou Terminal
- **Recuperação de lixo** — detecta e processa até sessões deletadas (`.jsonl.deleted`)
- **Agrupamento por hora** — sessões na mesma hora ficam no mesmo arquivo
- **Nomes semânticos** — `YYYY-MM-DD-HH-MM-<slug>.md` gerado a partir da conversa
- **Modo delta** — processa apenas sessões novas por padrão

## Uso

```bash
# Processar sessões novas (padrão)
python scripts/miner.py <raiz-do-agente>

# Re-processar tudo (ignora estado anterior)
python scripts/miner.py <raiz-do-agente> --full

# Filtrar por agente específico
python scripts/miner.py <raiz-do-agente> --agent meta-specialist

# Listar agentes disponíveis e destino de output
python scripts/miner.py <raiz-do-agente> --list

# Preview seguro: lista sessões pendentes para validação
python scripts/miner.py <raiz-do-agente> --dry-run
```

## Como Funciona (Fluxo de Dados)

```
<raiz>/.openclaw/
├── agents/<agente>/sessions/
│   ├── *.jsonl                        ← sessões ativas (entrada)
│   └── *.jsonl.deleted.*              ← sessões removidas (entrada resgatada)
└── Saída de Notas (Automática):
    ├── Para subagentes: .openclaw/workspaces/<agente>/memory/
    └── Para o "main": Prioriza .openclaw/workspace/memory/ (se existir) 
                        ou .openclaw/workspaces/main/memory/ (se não)
```
Skill Folder:
└── data/state.json                    ← controle de estado (delta) centralizado na skill
```

1. Lê cada `.jsonl` e extrai mensagens com `role`, `text`, `timestamp`
2. Detecta o canal (`discord`, `whatsapp`, `cron`, `terminal`)
3. Agrupa sessões que ocorreram na mesma hora (`YYYY-MM-DD-HH`)
4. Gera um slug descritivo (máx. 5 palavras) a partir do conteúdo
5. Salva no formato Raw-First com separadores `---` entre sessões agrupadas

## Formato de Saída

```markdown
# Sessão: 2026-02-04
**Canal:** discord | **Modelo:** gemini-3-flash | **Sessão:** 3adb...

---

[2026-02-04 19:00] **Eduardo:**
Texto exatamente como foi enviado...

---

[2026-02-04 19:00] **Agente:**
Resposta exatamente como foi gerada...
```

## Estrutura da Skill

```
memory-miner/
├── SKILL.md              # Este arquivo
├── data/
│   └── state.json        # Estado delta de todos os projetos processados
└── scripts/
    ├── miner.py          # CLI entry point (argparse + comandos)
    ├── models.py         # Dataclasses (Message, Session) e constantes
    ├── parser.py         # Parsing de JSONL e detecção de canal
    ├── formatter.py      # Renderização Markdown, slug e escrita de notas
    └── state.py          # Controle delta e descoberta de agentes
```
