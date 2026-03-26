---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy. Also use proactively whenever the user mentions "create a skill", "new skill", "add capability", "turn this into a skill", "package this workflow", or wants to extend the agent with reusable instructions — even if they don't explicitly say "skill".
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process goes like this:

1. Decide what the skill should do and roughly how
2. Write a draft
3. Test it with realistic prompts
4. Evaluate results (qualitative + quantitative)
5. Improve based on feedback
6. Repeat until satisfied
7. Optimize the description for accurate triggering
8. Package and deliver

Your job is to figure out where the user is in this process and help them progress. Maybe they want to create from scratch. Maybe they already have a draft and want to iterate. Be flexible — if the user says "just vibe with me", skip the formal evals.

---

## Communicating with the User

Pay attention to context cues about the user's technical level. The power of AI is inspiring people across all backgrounds to build. In the default case:

- "evaluation" and "benchmark" are borderline, but OK
- For "JSON" and "assertion", see serious cues before using without explaining
- Briefly explain terms if in doubt

**Language:** Always respond in the user's language. Code/variables stay in English.

---

## Mode Detection: LITE vs FULL

Before starting, assess the complexity of the requested skill:

```
User request received
       │
       ├─ Simple skill? (1-2 files, no scripts, clear purpose)
       │   Example: "skill for commit messages", "skill for naming variables"
       │   → LITE MODE
       │
       ├─ Complex skill? (scripts, multi-references, needs iteration)
       │   Example: "skill that analyzes documents and generates reports"
       │   → FULL MODE
       │
       └─ Unclear?
           → Ask: "This could be simple or complex. Want me to go
              fast (LITE) or with full quality testing (FULL)?"
```

**User can force:** `"quero modo completo"` → FULL | `"faz rápido"` → LITE

---

## LITE MODE — Quick Skill Creation

For simple, focused skills. Target: fast delivery, solid quality.

### Step 1: Capture Intent

1. What should this skill enable the agent to do?
2. When should this skill trigger? (keywords, contexts)
3. What's the expected output format?

If the current conversation already contains a workflow the user wants to capture ("turn this into a skill"), extract answers from the conversation history first.

### Step 2: Choose Location

Ask the user where the skill should live:

| Location | Scope | When to Use |
|----------|-------|-------------|
| `<workspace-root>/.agent/skills/<skill-folder>/` | Workspace-specific | Project-specific workflows |
| `~/.gemini/antigravity/skills/<skill-folder>/` | Global | Personal utilities |

**Default**: Ask if not specified.

### Step 3: Write the SKILL.md

Follow the Skill Writing Guide (below) to create the skill. For LITE mode:

- Keep SKILL.md under 200 lines
- Include frontmatter with pushy description
- Add clear "When to Use" section with triggers
- Write actionable instructions
- Include 1-2 examples if helpful

### Step 4: Add Resources (if needed)

- Scripts in `scripts/` — run `--help` first, treat as black boxes
- References in `references/` — loaded into context as needed
- Assets in `assets/` — templates, icons, fonts

### Step 5: Validate (Checklist)

Run through the End-to-End Checklist (below) before delivering.

### Step 6: Deliver

Tell the user the skill is ready, where it lives, and how to trigger it.

---

## FULL MODE — Iterative Skill Development

For complex skills that benefit from testing, benchmarks, and iteration.

### Phase 1: Capture Intent & Interview

Same as LITE Steps 1-2, but go deeper:

1. What should this skill enable the agent to do?
2. When should this skill trigger? (keywords, contexts)
3. What's the expected output format?
4. Should we set up test cases? (Yes for objectively verifiable outputs; optional for subjective ones)

Proactively ask about:
- Edge cases
- Input/output formats
- Example files
- Success criteria
- Dependencies

Check available MCPs for research. Come prepared with context to reduce burden on the user.

### Phase 2: Write the SKILL.md

Follow the Skill Writing Guide (below). For FULL mode, you can go up to 500 lines.

### Phase 3: Test Cases

After writing the draft, create 2-3 realistic test prompts — things a real user would actually say. Share them: "Here are a few test cases I'd like to try. Look right, or should I add more?"

Save test cases to `evals/evals.json`:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `references/schemas.md` for the full schema.

### Phase 4: Run & Evaluate

**This section is one continuous sequence — don't stop partway through.**

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Organize by iteration (`iteration-1/`, `iteration-2/`, etc.) and test case (`eval-0/`, `eval-1/`, etc.).

#### Step 1: Spawn runs (with-skill AND baseline) in the same turn

For each test case, spawn two subagents simultaneously — one with the skill, one without. Launch everything at once.

**With-skill run:**
```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what the user cares about>
```

**Baseline run** (same prompt, but depends on context):
- **Creating new skill**: no skill at all → save to `without_skill/outputs/`
- **Improving existing skill**: old version → snapshot first, then use snapshot → save to `old_skill/outputs/`

Write `eval_metadata.json` for each test case. Give each eval a descriptive name.

#### Step 2: While runs are in progress, draft assertions

Don't wait — draft quantitative assertions and explain them to the user. Good assertions are objectively verifiable and have descriptive names. Don't force assertions onto subjective skills.

Update `eval_metadata.json` and `evals/evals.json` with assertions.

#### Step 3: Capture timing data

When each subagent completes, save `total_tokens` and `duration_ms` to `timing.json` immediately — this data isn't persisted elsewhere.

#### Step 4: Grade, aggregate, and launch viewer

Once all runs complete:

1. **Grade** — spawn grader (reads `agents/grader.md`). Save to `grading.json`. Use fields `text`, `passed`, `evidence`.

2. **Aggregate** — run:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```

3. **Analyst pass** — read benchmark data and surface patterns (see `agents/analyzer.md`).

4. **Launch viewer**:
   ```bash
   nohup python <skill-creator-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   For iteration 2+, also pass `--previous-workspace`.
   For headless environments: use `--static <output_path>`.

5. **Tell the user**: "Results are in your browser — 'Outputs' tab for test cases, 'Benchmark' tab for quantitative comparison."

#### Step 5: Read feedback

Read `feedback.json`. Empty feedback = looks good. Focus improvements on specific complaints.

```bash
kill $VIEWER_PID 2>/dev/null
```

### Phase 5: Improve & Iterate

This is the heart of the loop. Key principles:

1. **Generalize from feedback.** The skill will be used across many prompts — don't overfit to test cases. If there's a stubborn issue, try different metaphors or patterns.

2. **Keep the prompt lean.** Remove things not pulling their weight. Read transcripts — if the skill wastes time on unproductive steps, trim those parts.

3. **Explain the why.** LLMs are smart. Explain reasoning instead of heavy-handed MUSTs. If you find yourself writing ALWAYS/NEVER in caps, reframe as a principle.

4. **Look for repeated work.** If all test runs write similar helper scripts, bundle that script in `scripts/`.

After improving:
1. Apply improvements
2. Rerun all test cases into new `iteration-<N+1>/`
3. Launch reviewer with `--previous-workspace`
4. Wait for feedback
5. Read, improve, repeat

Stop when: user is happy, feedback is all empty, or progress plateaus.

### Phase 6: Description Optimization

See the Description Optimization section below.

### Phase 7: Package & Deliver

See the Packaging section below.

---

## Skill Writing Guide

### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) — Always in context (~100 words)
2. **SKILL.md body** — Loaded when skill triggers (<500 lines ideal)
3. **Bundled resources** — Loaded as needed (unlimited, scripts execute without loading)

**Key patterns:**
- Keep SKILL.md under 500 lines (LITE: under 200)
- Reference files clearly with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

### Decision Trees

Help the agent choose the right approach:

```markdown
## Decision Tree

1. Is this a new project?
   - Yes → Follow "New Project Setup"
   - No → Continue to step 2
2. Does the project have existing tests?
   - Yes → Follow "Adding to Existing Tests"
   - No → Follow "Initial Test Setup"
```

### Scripts as Black Boxes

If your skill includes scripts, instruct the agent to run them with `--help` first:

```markdown
## Using the Helper Script

Run `./scripts/generate.sh --help` to see available options before using.
```

### Writing Style

- Use the imperative form in instructions
- Explain the **why** behind instructions — reasoning > rigid constraints
- Theory of mind: make instructions general, not super-narrow to specific examples
- Write a draft, then review and improve with fresh eyes

### Writing Effective Descriptions

The description is the primary triggering mechanism. Make it **pushy** — Claude tends to "undertrigger" skills.

**Good descriptions:**
- Are specific about what the skill does
- Include "when to use" scenarios
- List relevant keywords
- Are in third person
- Explicitly tell the agent to trigger even for edge cases

✅ Good: `"Analyzes legal documents and explains them in plain language. Highlights problematic clauses, assigns risk scores, and suggests questions before signing. Use this skill proactively whenever the user shares any legal document, contract, or terms of service — even if they simply ask 'what does this mean?' about a clause."`

❌ Bad: `"Helps with legal documents"`

### Providing Clear Triggers

```markdown
## When to Use This Skill

This skill is relevant when the user mentions:
- "create tests", "add tests", "write tests"
- "test coverage", "unit tests"
```

### Handling Edge Cases

Include a handling table for non-obvious scenarios:

```markdown
## Handling Edge Cases

| Situation | How to Handle |
|---|---|
| **Partial input** | Analyze what was provided. Note it's incomplete. Offer to continue. |
| **Very long input** | Focus on highest-impact sections. State what was skipped. |
| **User seems confused** | Be reassuring. Explain that understanding is power. |
```

---

## Output Rules (MANDATORY for every skill created)

Every skill created by skill-creator MUST include explicit output handling:

1. **Define where outputs go.** The SKILL.md must have a clear section specifying where results are saved.

2. **Ask the user for the output path** before starting any processing that generates files.

3. **Never save to default OS locations** (Desktop, Downloads, User home) without explicit permission.

4. **All artifacts (JSON, MD, reports, extracted files)** must be saved to the user-specified output directory.

5. **When generating a new skill, include** this boilerplate in the generated SKILL.md:

```markdown
## Output

Before processing, confirm the output directory with the user:
- **If specified:** Use the given path
- **If not specified:** Use the current workspace directory
- **NEVER** save to the user's home directory without permission

All generated files (reports, JSON, extracted data) go to the confirmed output path.
```

> This rule exists because without it, skills systematically save outputs to unpredictable locations, forcing the user to manually find and move files. Every skill should handle this explicitly.

---

## End-to-End Validation Checklist

**Run through this before delivering ANY skill (LITE or FULL):**

| # | Check | How to Verify |
|---|-------|--------------|
| 1 | YAML frontmatter is valid | `name` + `description` present, valid YAML |
| 2 | Description is pushy and specific | Not generic ("helps with X") |
| 3 | "When to Use" section exists with clear triggers | Keywords, phrases listed |
| 4 | All referenced files exist | Check every path mentioned in SKILL.md |
| 5 | Scripts execute without error | `python script.py --help` succeeds |
| 6 | Output path is defined in the skill | Has an "Output" or equivalent section |
| 7 | Tested with at least 1 real prompt (LITE) or 2-3 (FULL) | Output matches expectations |
| 8 | SKILL.md ≤ 500 lines (LITE ≤ 200) | Line count check |
| 9 | No security violations | No hardcoded secrets, no malware |

Run `scripts/quick_validate.py <skill-path>` for automated structural validation.

---

## Description Optimization

After creating or improving a skill, offer to optimize the description for better triggering.

### Step 1: Generate trigger eval queries

Create 20 eval queries — mix of should-trigger (8-10) and should-not-trigger (8-10). Save as JSON.

**Should-trigger queries:** different phrasings, casual and formal, edge cases where the skill is needed but not explicitly named.

**Should-not-trigger queries:** near-misses that share keywords but need something different. Avoid obviously irrelevant queries.

Queries must be realistic and specific — file paths, personal context, abbreviations, typos, casual speech.

### Step 2: Review with user

Present eval set using `assets/eval_review.html` template. Replace placeholders:
- `__EVAL_DATA_PLACEHOLDER__` → JSON array
- `__SKILL_NAME_PLACEHOLDER__` → skill name
- `__SKILL_DESCRIPTION_PLACEHOLDER__` → current description

### Step 3: Run optimization loop

```bash
python -m scripts.run_loop \
  --eval-set <path> \
  --skill-path <path> \
  --model <model-id> \
  --max-iterations 5 \
  --verbose
```

### Step 4: Apply result

Take `best_description` from JSON output and update SKILL.md frontmatter. Show before/after and report scores.

---

## Advanced: Blind Comparison

For rigorous comparison between two skill versions: read `agents/comparator.md` and `agents/analyzer.md`. Optional, requires subagents, most users won't need it.

---

## Packaging

### Standard (.skill file)

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

This validates the skill first, then creates a distributable `.skill` file.

### Updating an Existing Skill

- **Preserve the original name** — don't rename to `-v2`
- **Copy to a writable location** before editing if installed path is read-only
- **If packaging manually**, stage in `/tmp/` first

---

## Environment-Specific Instructions

### Claude.ai

- No subagents → run test cases yourself, one at a time
- Skip baseline runs and quantitative benchmarking
- Present results directly in conversation
- Skip description optimization (requires `claude -p` CLI)
- Packaging works — user can download the `.skill` file

### Cowork

- Subagents available → full workflow works
- No browser → use `--static <output_path>` for eval viewer
- Feedback via downloaded `feedback.json`
- Description optimization should work via `claude -p`

---

## Reference Files

| Path | When to Read |
|---|---|
| `agents/grader.md` | Spawning grader subagent (Phase 4) |
| `agents/comparator.md` | Blind A/B comparison (Advanced) |
| `agents/analyzer.md` | Analyzing benchmark results (Phase 4) |
| `references/schemas.md` | JSON structures for evals, grading, benchmarks |

---

**Core loop reminder:**

1. Figure out what the skill is about (LITE or FULL)
2. Draft or edit the skill
3. Test with realistic prompts
4. Evaluate: `eval-viewer/generate_review.py` + quantitative evals
5. Improve and repeat
6. Validate E2E checklist
7. **Ensure output rules are baked into the skill**
8. Package and deliver

Good luck! 🚀
