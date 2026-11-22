# Dedicated lesson writer

Every new lesson and substantial rewrite follows four steps. The parent handles the conversation, gathers sources, checks the result and publishes it; it never writes the teaching itself.

1. **Pick the best model.** For each lesson, search online for the model that is currently best at writing clear, easy-to-understand lessons, and use the best one the user can call.
2. **A separate writer agent writes the lesson.**
3. **A fresh tone editor on the same model edits prose only.**
4. **Answers are recomputed independently before publishing.**

A direct user request for a model overrides step 1. `bin/lesson_routing.py` is optional: when a policy file exists (`${XDG_CONFIG_HOME:-$HOME/.config}/blackboard/lesson-routing.json` or `$WS/.blackboard/lesson-routing.json`), `resolve` names the author model and effort to use instead of the search; `check` validates a receipt against it.

## 1. Pick the model

1. List every model the user can call right now: the current host's live delegation tool schema or model picker, plus any other installed, signed-in CLI (`claude`, `codex`; check its `--help` or model list). A model on another installed host is eligible. Never sign up for, buy, or change a subscription.
2. Run 2 to 4 targeted searches: release notes for each provider's newest models, human-preference writing boards, teaching or tutoring evals that cover current models, and credible side-by-side comparisons of explanation clarity. Weight teaching evals, human writing preference and this user's recorded lesson feedback over reasoning scores; never rank by coding scores. Skip models nobody can call yet. If the user does not have the winner, take the best-ranked model they do have. Within one session, reuse a search younger than 24 hours.
3. Use effort `medium` for a straightforward lesson and `high` for dense multi-step derivations or unfamiliar material.
4. Tell the user once: "Writing with <model> at <effort>", plus one short clause on why.

If browsing is unavailable, use the strongest available writing model, say the search was unavailable, and never invent a ranking. Model names are examples, not defaults: resolve exact callable IDs at runtime.

## 2. Dispatch the writer

Prefer the host's native agent tool when it can set the selected model and effort; inspect its actual schema.

- **Codex app:** `spawn_agent` (or its equivalent) with `model` and `reasoning_effort`. Never a full-history fork that inherits the parent's model.
- **Claude Code:** the Agent tool with an explicit model and effort; otherwise a headless `claude -p --model <id> --effort <level> --output-format json` writer.
- Pass prompts through stdin or structured arguments, never shell interpolation. If the writer cannot edit the file, it returns the blocks and the parent saves them unchanged.

If the writer fails, pick the next best model, say so in one line, and launch another writer. Never let the parent quietly write the lesson.

**Briefing.** Give the writer: the role line `Role: Blackboard lesson writer. Writer already selected; do not run model selection or spawn another writer.`; absolute lesson and workspace paths and a bounded write scope; the topic, language, target exam, prior knowledge and teaching preferences; absolute paths to SKILL.md, TEMPLATES.md, QUIZ.md, **the blueprint file the writer must follow** (`BLUEPRINT-STEM.md`, `BLUEPRINT-HUMANITIES.md` or `BLUEPRINT-FUN.md`, as SKILL.md **Lesson blueprints** picks), the mission, learning records and every source file. The blueprint, TEMPLATES.md and QUIZ.md hold every lesson and practice rule; the briefing points to them and does not restate them. The writer streams body blocks; the parent owns the browser and the final render. Never let two agents write the file at once.

## 3. Tone pass

When the writer is done, a fresh agent on the same model and effort edits the lesson for tone and order. Do not fork the writer's conversation.

- **Briefing:** the lesson path, the path to TEMPLATES.md (**Tone** and **Top to bottom**), and `Role: Blackboard tone editor. Do not run model selection, spawn agents, or add new teaching content.`
- **What it does:** rewrites prose to the Tone rules and the **Hard-to-read patterns** table; deletes what TEMPLATES.md **What a lesson leaves out** lists; moves each explanation above the first use of its term and bolds the term there; runs `python3 bin/prose_lint.py <lesson>` and fixes every real warning.
- **What it must not change:** math, code blocks, `::: fig` and `::: interactive` specs, `::: mcq` and `::: checkin` questions, options and keys, front matter, headings and the `::: sources` block.
- **Parent checks:** copy the writer's version to `$WS/reference/lesson-NNNN.draft.md` first, diff afterwards, and revert any hunk that touches the list above. If the pass fails, keep the writer's version and say so in one line.

## 4. Completion

Before publishing, a fresh agent recomputes every worked answer and quiz key independently of the writer and of the official key; the writer fixes what it finds. Then verify source coverage, chapter links, figures, math, the banner and the byline (`model:` is the actual writer's full name). Keep prompts and model-selection details out of the lesson body. This route applies only to new lessons and substantial rewrites; it does not change the chat, quiz, Explain or definition workers.
