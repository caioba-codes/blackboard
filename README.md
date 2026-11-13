# Blackboard

My teaching skill for Claude Code and Codex. You ask for a lesson and it writes it on a black board in your browser: math one step per line, real photos, chalk diagrams, and a quiz at the end. Highlight anything you don't get and ask why. If any part of it sucks, open a PR.

![board](board/screenshot.png)

**Install**

```bash
git clone https://github.com/caioba-codes/blackboard ~/.claude/skills/blackboard
cd ~/.claude/skills/blackboard && npm install
```

For Codex, clone it to `~/.codex/skills/blackboard` instead. It updates itself once a day.

**Use it**

```
/blackboard learn how the NVIDIA DGX Spark works
/blackboard learn u-substitution for MATH 1552
```

The first one teaches from primary sources. The second uses your course files (syllabus, past exams, homework) and teaches only what's on the test.

If something doesn't work, run `bin/doctor.sh`.

MIT license.
