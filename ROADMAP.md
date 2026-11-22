# Blackboard roadmap

Open items only. Shipped: the XP health bar that fills only with verified answers, 8-bit sparks and sounds on right answers (the user asked for them), the chat panel.

- **Gold rule in the hub** for a lesson whose XP bar is full.
- **Redo rounds (not built yet):** the board logs which Your turns, drill, practice-exam problems and flashcards were missed; a study session opens with them before the next new chapter, and a later round shows only the misses until a round adds none (BLUEPRINT-STEM.md, BLUEPRINT-HUMANITIES.md).
- **Per-chapter video follow-ups:** a player that is open when a new chapter video lands says "reload the page to play it" instead of adding it in place; Watch lists the chapters not ready yet in its intro line, not as greyed zones on the seek bar.
- **Retention line:** when a card missed earlier is answered right a week later, one line: "You missed this on 9/8. Right today."
- **Quiet streaks:** a small "3 days" mark beside the folder name in the hub. No notifications.
- **`/progress` ledger:** lessons finished, items answered, accuracy by topic, a heatmap of days.
- **Handwriting:** grade a photo of handwritten work inline under the block, against the course rubric.
- **Practice deck from a review sheet.**
- **Tablet layout** (the board is plain HTTP, so it can be served over a LAN).
- **Timed exam mode:** n problems, a clock, then the rubric check.

Everything keys off `learning-records/quiz-log.jsonl` and dates, never off a specific course.
