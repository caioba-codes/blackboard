# Hosts

The skill has one core and a thin host layer. Two axes are detected separately, never asked:

| Axis | Detect | Values |
|---|---|---|
| **agent** | `BLACKBOARD_AGENT` override → `CLAUDECODE=1` → `claude`; `CODEX_THREAD_ID` or `CODEX_HOME` → `codex`; else `claude` | `claude`, `codex` |
| **layout** | `BLACKBOARD_LAYOUT` override → `CMUX_WORKSPACE_ID` set → `cmux` → `CODEX_INTERNAL_ORIGINATOR_OVERRIDE=Codex Desktop` → `app`; else `tab`. | `cmux`, `app`, `tab` |

`board/render.sh` computes both and writes them into `~/.cache/blackboard/state.json` (`agent`, `layout`) so `bridge.py` and the scripts agree.

## What differs

| | tab (Claude Code / Codex CLI) | app (Codex desktop) | cmux (either agent) |
|---|---|---|---|
| Board display | `open http://127.0.0.1:7331` once in the default browser | agent creates and navigates an in-app Browser tab, marks it deliverable, then presents that exact tab on the right with `codex_app__open_in_codex` | `cmux new-surface --type browser --url http://127.0.0.1:7331` once in the right pane; tab title "Blackboard" |
| LMS pull browser | Claude uses its Chrome extension; Codex uses the token path (`bin/lms-pull.sh`) or manual drop | token path (`bin/lms-pull.sh`) or manual drop | `cmux browser` (`import --from chrome` once, then `eval` / `download`) |
| Voice (Speak on a flashcard) | page → bridge `/api/listen` → `bin/listen.sh` | same | same |
| Explain, quiz generation, quiz grading | headless in the bridge (`bin/explain.py`, `bin/quiz.py`) | same | same |

## Codex app (layout=app)

The Codex desktop app has a browser panel beside the chat. `render.sh` detects the app from `CODEX_INTERNAL_ORIGINATOR_OVERRIDE=Codex Desktop` and never calls macOS `open` for this layout. After the first successful render, the agent uses the in-app Browser tool to create a tab and navigate it to the board URL, verifies the lesson title, and calls `markDeliverable()` on it. It then calls:

```text
codex_app__open_in_codex({
  target: {type: "browser", tabId: "<Browser tab.id>"},
  placement: "right"
})
```

The app action may report `queued`; finish the turn so it can present the tab. Call it once per task and keep that tab. The board refreshes over SSE after every later render. Never substitute a provider/app tab id from `user.openTabs()` for the Browser tab's own `tab.id`; that can select a blank tab. `~/.codex/prompts/blackboard.md` turns `/blackboard …` into this skill for Codex. A read-only task must say so in one line and stop.

The Browser and `codex_app__open_in_codex` tools may be deferred. Find them by exact name in the available tool catalog before treating them as unavailable.

## Command syntax per agent

- Claude Code: `/blackboard explain e3 L48 "text"`
- Codex: `$blackboard explain e3 L48 "text"`

`bridge.py` builds the command from `~/.cache/blackboard/state.json`. Nothing else in the skill depends on the host.

## What is host-independent

Everything the student touches on the page is the same local document in all three layouts: the flashcard box, the Speak button, Validate, the topic and mode chips, the loading shimmers. The board is served from `127.0.0.1` to a browser on the same machine, so the mic can live on the bridge and use on-device Apple Speech rather than the browser's Web Speech API, which exists only in Chrome and would fail in the cmux WKWebView.

Explain, quiz generation and quiz grading run headless inside the bridge. Nothing is sent to the chat, so they work the same everywhere. Clicks are logged by the bridge; nothing on the page wakes the agent.

## Recommended setups

- Non-technical users: Claude Code desktop or the Codex app, run from the folder with the course files. The board opens beside the chat.
- Power users: cmux, agent on the left, board pane on the right.

## Headless host (no screen)

When the agent runs on a machine nobody is looking at, render as usual (`board/render.sh`, bridge on 127.0.0.1:7331), then ship a picture of the board through whatever channel reaches the user (chat, email, a messaging bot):

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1280,1600 --screenshot=/tmp/board.png http://127.0.0.1:7331/ 2>/dev/null
```

Keep the bridge up so a later `/blackboard` command edits the same lesson. Never open a browser window on a headless host just to render the board.


## Lesson writer routing

New lessons and substantial rewrites always use a dedicated writer agent selected independently of the parent chat model. Follow [LESSON-WRITER.md](./LESSON-WRITER.md) before authoring: quick evidence/availability check, explicit model and effort, host-native delegation or a headless same-host writer, then parent verification. Never change the parent session model or global defaults.
