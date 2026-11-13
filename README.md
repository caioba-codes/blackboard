# Blackboard

A teaching skill for Claude Code and Codex. You ask for a lesson, the agent writes it on a black board in your browser: derivations one step per line, real photos of the thing, chalk diagrams, a quiz at the end. Select any sentence and ask why. Nothing gets pasted into your chat.

![board](board/screenshot.png)

## Why not just ask in chat

Chat is fine for a quick answer, but it's a bad place to learn math. Here the lesson shows the column typeset, and the chat answer to "what was done to get these?" comes back as raw `e^{2x} → 1/2 e^{2x}`. That's harder to read than the lesson it explains.

![a chat answer full of unrendered math](board/chat-example.png)

On the board the same answer is written one step per line, rendered, with the reason beside each step, inside the lesson it belongs to.

## Install

Clone it into your skills folder, then install the figure dependencies once:

```
git clone https://github.com/caioba-codes/blackboard ~/.claude/skills/blackboard
cd ~/.claude/skills/blackboard && npm install
```

For Codex, clone it to `~/.codex/skills/blackboard` instead (or both). On macOS the first lesson also sets up a small background service that keeps the board running at `http://localhost:7331` and adds a **Blackboard** app to your Dock.

### Updates

A cloned install updates itself. At most once a day, when you use the skill, it fetches this repo and fast-forwards to the latest version (8-second limit, silent when offline). When it updates, it tells you in one line and reinstalls or restarts what changed. It never touches a checkout with local edits. Turn it off with `BLACKBOARD_UPDATE=0`. Check right now with `BLACKBOARD_UPDATE=force bin/update.sh`.

`npx skills@latest add caioba-codes/blackboard` works too, but it installs a copy that does not update itself.

Then, from any folder with your material in it:

```
/blackboard learn how the NVIDIA DGX Spark works
/blackboard learn u-substitution for MATH 1552
```

The first line is self-study: it reads primary sources and writes the lesson. The second is course mode: it uses your own files (syllabus, past exams, homework) and tags every block with the exam problem it serves.

## What you get

1. One board page at `http://127.0.0.1:7331`, one lesson at a time, written block by block while you watch.
2. One STEM lesson template ([example](examples/stem/learn/lessons/0001-how-to-ace-your-second-integral-calculus-test.md)): the tool, how to choose, one labeled worked example, your turn. One operation per line, the reason in the margin, the answer boxed. A non-STEM template comes later.
3. Explain on select. Highlight words, click Explain. A chalk callout appears below the paragraph, with a lightbulb and title that fold and expand its body. A small × removes it.
   Highlight 1-5 words and click Definition instead for a small popup with what the term means in this lesson. Answers come back in about a second, or instantly for terms the lesson defines and for the ones precomputed in the background while you read. The selected term keeps a dotted underline; click it again to reopen the popup. These anchors survive reloads in the same browser. Nothing is written to the lesson file.
4. A quiz at the end of every lesson. Multiple choice built in, flashcards on demand, graded by voice or text.
5. Photos when the subject is a physical thing. The object itself as the banner, its parts beside the sections that discuss them.
6. A hub across every folder on the machine. Search, recent, this folder, the others.
7. A map of every lesson: a scale down the right edge with a mark per section, filled as you read, and an XP health bar in the corner that fills only with right answers and opens the Contents (press `t`).
8. Homework is never solved for you unless you ask for exactly that.

## Requirements

- macOS or Linux, Python 3.10+
- `claude` (Claude Code) or `codex` on PATH. Explain and quiz grading run headless through it.
- `node` for the chalk figures (roughjs). `npm install` in this folder once.
- Optional: `pandoc` + `tectonic` (worksheets to PDF), `yt-dlp` (transcripts), `pdftotext`, `manim`.
- Voice answers need macOS (on-device Apple Speech).

Run `bin/doctor.sh` to check all of it.

## Hosts

- Claude Code or Codex desktop: the board opens beside the chat.
- cmux: the board is a tab in your browser pane, pinned to the folder you are working in.
- Plain terminal: a browser tab.
- Headless machine: render, screenshot, send the picture. See `HOSTS.md`.

## Files

`SKILL.md` is what the agent reads. `TEMPLATES.md` is the writing contract. `QUIZ.md`, `EXAM-MODE.md`, `LMS.md`, `FIGURES.md`, `HOSTS.md` cover the rest. `board/` is the server and the page. `bin/` holds the headless writers and helpers. `ROADMAP.md` is what comes next.

## License

MIT
