# Dedicated lesson writer

Every new lesson and substantial lesson rewrite is authored by a separate writer agent, even when the parent already uses the chosen model. The parent handles the conversation, gathers sources, checks the result, and publishes it. This instruction authorizes lesson-writing delegation; it does not authorize unrelated parallel work, new user-facing tasks, or changes to the user's global model settings.

**Long vs short.** A long lesson is a new lesson or substantial rewrite with two or more chapters. Only long lessons get the live web check (step 3) and the automatic-selection decision receipt (step 5). Every lesson, long or short, gets the tone pass. A short lesson (one chapter) still picks and dispatches a writer. Every explicitly routed lesson gets a routing receipt, regardless of length.

## Explicit role policy

Before ranking models, run `python3 bin/lesson_routing.py resolve --workspace "$WS"` from the skill directory. The default per-user file is `${XDG_CONFIG_HOME:-$HOME/.config}/blackboard/lesson-routing.json`; an optional `$WS/.blackboard/lesson-routing.json` replaces it for that workspace. These files live outside the skill checkout, so `bin/update.sh` and skill updates must never delete or overwrite them. The format is:

```json
{"version":1,"roles":{"author":{"model":"provider-exact-author-id","effort":"high"},"reviewer":{"model":"provider-exact-reviewer-id","effort":"medium"},"support":{"model":"provider-exact-support-id","effort":"medium"}}}
```

For example, a Codex host that actually offers these IDs could set `author` to `gpt-6-astra` with `medium`, `reviewer` to `gpt-6-sol` with `high`, and `support` to `gpt-6-sol` with `high`. This is an example of configuration, not a claim that either model is best or currently callable. Use exact IDs and supported effort values from the current host. A direct user request outranks workspace policy, which outranks per-user policy, which outranks automatic selection. For a direct request, write a temporary JSON file in the same format containing only the requested roles and pass `--override <path>` to both `resolve` and `check`. Each named role must give both model and effort. Never infer an omitted effort or inherit the parent session's settings.

The resolver rejects `inherit`, `default`, `auto`, and `automatic` in either field, ignoring case; `none` remains a valid explicit effort when the host supports it. An absent default policy permits automatic selection, but an explicitly named missing `--user-config` or `--workspace-config` file blocks resolution.

If `resolve` returns `explicit`, use its requested model and effort for each selected role. Skip the model-fit ranking and live ranking search for those roles; verify their callability and runtime identity through the host before dispatch. General fleet defaults do not override this lesson policy. The author owns structure, explanations, worked examples, quiz items, substantive revisions, and tone. Support may extract/index sources, check format, or render; support never authors teaching. A fresh reviewer agent, independent of the author and tone editor, recomputes physics, code, answer keys, and source coverage. Give findings to the author to resolve, then have the reviewer verify resolution. The tone pass stays a fresh agent on the author's exact model and effort.

For every explicit route, save `$WS/reference/lesson-writer-NNNN.json` with `selection` equal to the resolver output, `long_lesson` true or false, and `runs` containing `author` and `reviewer`, plus `support` only if used. Each run records `requested` and `resolved` objects with `model` and `effort`, taken from dispatch parameters and actual host runtime metadata, plus `outcome` (`complete` for author/support, `passed` for reviewer). The reviewer run also needs `fresh_agent: true` and `findings_resolved: true`. Every lesson requires a `tone_editor` run with `fresh_agent: true`, `outcome: "complete"`, and the same requested/resolved identity as the author. Do not treat a byline or a model's self-description as runtime evidence. Run `python3 bin/lesson_routing.py check --workspace "$WS" --receipt "$WS/reference/lesson-writer-NNNN.json"` (and the same `--override` if used) before final render/publication. The CLI compares the supplied evidence to the current policy; agents must obtain trustworthy runtime metadata and confirm the review work occurred. If metadata is unavailable, a required model or effort is unsupported, or `check` fails, preserve the existing lesson and report the concrete blocker. Do not substitute another model. Independent source extraction or formatting support may continue.

If the resolver returns `automatic`, continue with the quick check below and the existing automatic fallback. A malformed present policy is a blocker, never a reason to return to automatic selection.

## Quick check before every lesson

Do this only for roles without an explicit policy, before instructional prose is written. A title/loading shell can appear immediately while the parent checks the model. Do not inherit the parent's model or effort silently.

1. Identify the current host and its actual callable models and supported efforts from the live delegation tool schema, model picker/catalog, or installed CLI metadata. Claude Code chooses among available Claude models; Codex app/CLI chooses among available Codex models. Do not switch providers or subscriptions without an explicit user request. An explicit writer-model request overrides ranking, subject to availability.
2. Read the teaching/lesson row in `~/stuff/cortex/stack/model-fit.md` if it exists. Ignore `pending`/`stale` rows and evidence older than 7 days for this quick selection. This file is a candidate recommendation, not proof of account availability or a dedicated teaching benchmark. Do not use a global Claude winner as the Codex recommendation.
3. Long lessons only: make a brief live check (normally 1–3 targeted searches): current provider model availability/release notes, plus current independent evidence on explanation quality, instruction following, and reasoning relevant to the topic. Open the supporting pages. Prefer direct teaching evaluations and this user's recorded lesson feedback; general text preference and reasoning benchmarks are proxies, not proof of superior learning outcomes. Never rank by coding scores alone. Compare within the host's available models. If several lessons are authored in the same session, reuse an evidence check younger than 24 hours but recheck callable models and failures for each lesson.
4. Choose the strongest supported teaching candidate, not the cheapest parent model. Select effort explicitly: use supported `medium` as the normal starting point for a straightforward lesson; increase to `high` or a model-specific supported equivalent for dense multi-step derivations, unfamiliar technical material, or known reasoning failures. Higher effort is not evidence of clearer teaching; keep the same concise didactic contract. Use higher extremes only when the task or evidence justifies their latency. A candidate-specific evidenced effort recommendation takes precedence over this heuristic.
5. Long lessons only: save a small decision receipt to `$WS/reference/lesson-writer-NNNN.json` before dispatch: checked_at (UTC), host, lesson path, selected model ID, supported effort, evidence URLs/dates, confidence, why this candidate fits, and any fallback. Create `reference/` if needed. Record requested versus resolved model separately when runtime metadata supplies both. Never invent a resolved identity.
6. Tell the user once, briefly: “Writing with <model> at <effort>.” If no direct teaching comparison exists, call it the best-supported available choice, not an objectively proven best teacher.

If browsing is unavailable, use a recent qualifying recommendation and disclose that the live check was unavailable. With no recent evidence, use the strongest verified available general reasoning/writing model as a provisional choice and record low confidence. Never manufacture a ranking. Do not stop useful source gathering while selecting the writer.

Names such as Fable, Opus, Astra, Sol, and Luna are examples, not permanent defaults. Resolve exact callable IDs at runtime. Do not treat a model named in an old lesson as today's winner.

## Dispatch on the current host

Prefer the host's native agent tool when it supports the selected model and explicit effort. Inspect the tool's actual schema; do not invent parameters.

- **Codex app:** use the available `spawn_agent`/collaboration equivalent, passing the selected `model` and `reasoning_effort`. If the schema only permits overrides with `fork_turns: "none"` (or a partial fork), use that and include a complete briefing. Do not use a full-history fork that silently inherits the parent's model. Do not create a new sidebar task. While the writer works, the parent independently verifies source scope, prepares assets, or checks worked examples.
- **Claude Code:** use its Agent/subagent facility with an explicit supported model and effort if both can be set. If native delegation cannot select the exact model or effort, run a separate headless Claude Code writer with explicit `--model <id>` and `--effort <level>`. Check installed `claude --help` first. Never accept `inherit` or an implicit default as the selected model.
- **CLI fallback:** a separate headless writer process counts as the dedicated agent. Claude uses `claude -p --model <id> --effort <level> --output-format json`; Codex uses the host's approved launcher with explicit model and effort, never a raw execution command. Verify the installed help/schema before use. Supply prompts through stdin or structured tool arguments, not shell interpolation. Keep normal approval/sandbox boundaries. If the writer cannot edit the destination, have it return the authored blocks for the parent to save unchanged; do not relax permissions just to get an agent running.

Check the dispatch result, error status, and runtime model metadata before claiming success. A selected model may be listed yet unavailable due to account access or quota. Under automatic selection only, if the writer fails, select the next strongest eligible model **within the same host**, update the receipt, disclose the fallback in one line, and launch another writer. Under explicit policy or direct user request, report the failure without substitution; preserve existing content. Never let the parent quietly write the lesson when delegation failed.

## Writer briefing and ownership

Pass all of the following to the writer:

- `Role: Blackboard lesson writer. Writer already selected; do not run model selection or spawn another writer.` This prevents recursive delegation.
- Exact absolute lesson/workspace paths and bounded write scope. Existing user annotations, quiz records, unrelated lessons and global settings must be preserved.
- User's requested topic, language, demonstrated prior knowledge, target assignment/exam, time budget, and explicit teaching preferences.
- Absolute paths to SKILL.md, TEMPLATES.md, QUIZ.md, relevant mission/learning records, and all source files or inspected excerpts. Require source reading, source-matched quiz items, and answer verification.
- Selected model and effort, plus instruction to use actual runtime identity for the byline. The parent model must not appear as the author merely because it saves or renders the file.
- For a STEM lesson, TEMPLATES.md **STEM lessons** and the model lesson `examples/stem/learn/lessons/0001-how-to-ace-your-second-integral-calculus-test.md` (copy its structure): each method in the **Shape of each explanation** order (the tool, how to choose, ONE labeled worked example with a boxed answer, a hidden-answer "Your turn"); no verification paragraphs; every solution (Your turn, checkpoints, drills, practice exam, `why:` with work) in the same format, never equations chained through a sentence, and `bin/lint.py` clean; no opening hook, no chapter-opening preview or summary paragraphs, no exam logistics, no inline provenance tags, and an Exam Topics Breakdown for exam prep.
- Full lesson requirements: compact prerequisites, chapter contents, conditional prerequisite check-in, source-grounded teaching, diagrams wherever they make an explanation easier to visualize or understand, placed beside that explanation (not automatically at first mention), an `image:` subject taken from the lesson's own topic (never a chalkboard or classroom), unique banner, and streaming blocks. Child writes body blocks; parent owns browser navigation and the final render. Do not have both write the same file concurrently.
- Multiple choice: exactly four options per item (true/false keeps two), one correct, each distractor a real plausible mistake on that problem written as `- option || the mistake`, never a joke option; keys spread over all four positions (QUIZ.md **Multiple choice**).
- STEM lessons: every result produced by a rule (setup boxes, derivation steps, worked examples, your-turn answers) gets a tap-to-see hint, `\why{<math>}{<general rule>}`; the hint states the general rule, never the specific computation (TEMPLATES.md **STEM lessons**).
- Tabular content (cases, forms, comparisons) is always a markdown board table, never a KaTeX `\begin{array}`/`tabular` with `\hline` or `|` rules (TEMPLATES.md **Tables**; `bin/lint.py` flags it).
- Code blocks: every line at or under 60 characters; comments go on their own line above the statement, never trailing a long line.
- Questions with code (`::: mcq` stems, `::: checkin` questions and answers): more than one statement goes in a fenced ```java block with real indentation, then the question sentence on its own line. Never inline a class or several statements into a sentence.

The parent may create the initial metadata/loading shell without claiming to have authored the lesson. The writer can stream sequential blocks into the lesson when it has scoped access. When it returns blocks instead, save those blocks sequentially. Follow up with that same writer for substantial teaching corrections; parent edits are limited to mechanical integration and verification fixes, with authorship kept accurate.

## Tone pass (second agent)

Every lesson. When the writer finishes, a second agent edits it for tone and order before the completion check. Writing and editing are separate jobs, and a fresh reader catches drift that the writer approves in its own text.

- **Model:** the same model and effort the writer used, taken from the receipt. Dispatch it the same way as the writer. Run it only after the writer is done; never let two agents write the file at once.
- **Fresh context:** do not fork the writer's conversation. The briefing is the lesson path, the absolute path to TEMPLATES.md (sections **Shape of each explanation**, **Tone: easy to read top to bottom** and **Sequence meaning before use**), and this role line: `Role: Blackboard tone editor. Do not run model selection, spawn agents, or add new teaching content.`
- **What it does:** it reads the lesson top to bottom as a learner, then works through these steps:
  1. Rewrite prose sentences to follow the Tone rules. Check each sentence against the **Hard-to-read patterns** table, and split long sentences instead of shortening them.
  2. Fix the order so the lesson reads top to bottom. List every term, symbol and abbreviation with the line of its first use and the line of its explanation. Where the first use comes before the explanation, move the explanation up to before the first use (a short plain sentence there, or the whole explanation paragraph). Never fix it with a forward pointer such as "see below". Bold each term where it is explained.
  3. Where an explanation is out of Shape order, reorder paragraphs within its section.
  4. Run `python3 bin/prose_lint.py <lesson>` and fix every warning that is real. Leave a warning only when it is a false alarm (for example a 26-word sentence that is mostly math), and name it in your report.
- **What it must not change:** math (inline and display), equations, code blocks, `::: fig` and `::: interactive` specs, `::: mcq` and `::: checkin` questions, options and keys, front matter, headings, and the `::: sources` block. It edits prose only.
- **Parent checks:** before dispatch, copy the writer's version to `$WS/reference/lesson-NNNN.draft.md`. Afterwards, diff the two. Revert any hunk that touches something on the must-not-change list. Then run the completion check below.
- **Byline and receipt:** the byline stays the writer's. Add `tone_editor` (model, effort, outcome) to the receipt.
- **If it fails:** keep the writer's version, say so in one line, and continue to completion.

## Completion

Wait for the writer, reviewer, and any tone pass to finish. Verify coverage against sources, every quiz key, the prerequisite list, chapter links, diagrams and math, unique banner, and the actual writer byline. The fresh reviewer must independently recompute answers and coverage; send findings back to the author and confirm resolution. Rendering or model reputation is not proof of correctness. For explicit routing, record requested and resolved runtime identities and run the receipt check above before final render/publication. Keep prompts and model-selection details out of the student's lesson body.

This route applies to new lessons and substantial lesson rewrites. It does not switch the left-hand chat, regenerate existing lessons just because a new model launches, or change the separate quiz/Explain/definition workers unless explicitly requested.

Implementation references (verify again when host capabilities change):
- [Official OpenAI subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Claude Code custom subagents](https://code.claude.com/docs/en/sub-agents)
- Local `codex exec --help`, `claude --help`, and the live host tool schemas are authoritative for installed controls.
