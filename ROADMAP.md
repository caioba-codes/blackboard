# Blackboard roadmap

Open items only. Shipped: the XP health bar that fills only with verified answers, 8-bit sparks and sounds on right answers (the user asked for them), the chat panel.

- **Gold rule in the hub** for a lesson whose XP bar is full.
- **Boss quiz:** the final quiz stays dim ("reach the end") until the body has been scrolled through. Misses become the next lesson's check-in.
- **Retention line:** when a card missed earlier is answered right a week later, one line: "You missed this on 9/8. Right today."
- **Quiet streaks:** a small "3 days" mark beside the folder name in the hub. No notifications.
- **`/progress` ledger:** lessons finished, items answered, accuracy by topic, a heatmap of days.
- **Handwriting:** grade a photo of handwritten work inline under the block, against the course rubric.
- **Practice deck from a review sheet.**
- **Non-STEM lesson template** for conceptual and memorization courses.
- **Tablet layout** (the board is plain HTTP, so it can be served over a LAN).
- **Timed exam mode:** n problems, a clock, then the rubric check.

Everything keys off `learning-records/quiz-log.jsonl` and dates, never off a specific course.
