# RESOURCES.md Format

`RESOURCES.md` is the curated set of trusted sources for this workspace. Knowledge in lessons is drawn from here, never from parametric guesses. In course mode it is the only allowed source of content.

## Structure

```md
# ECE 2020 Resources

## Knowledge

- [Test 1 topic list — Canvas announcement 2026-09-01](sources/announcements/test1-topics.md)
  kind: topic-list · tier: 1 · Use for: what is in scope for Test 1.
- [Practice Test 1 (Spring 2026)](sources/exams/practice-test-1.pdf)
  kind: practice-exam · tier: 3 · Use for: practice problems on K-maps, SOP, timing.
- [HW2 — Boolean simplification](sources/hw/hw2.pdf)
  kind: hw · tier: 5 · assigned: yes · Use for: which skills are due; never solve its problems.
- [Week 2 Lecture 2 slides](sources/slides/week2-l2.pdf)
  kind: slides · tier: 6 · Use for: notation, the professor's step order.
- youtube: [3Blue1Brown — But what is a neural network?](https://www.youtube.com/watch?v=aircAruvnKk)
  transcript: sources/youtube/aircAruvnKk.txt · used-in: 0007 · Use for: intuition for layers and weights.

## Channels            # self-study only; edit freely

- 3Blue1Brown · math, ML intuition
- Ben Eater · digital logic, computers from scratch
- Computerphile · CS concepts
- MIT OpenCourseWare · full lectures
- Khan Academy · fundamentals

## Gaps

- No past exams for Test 1 yet. Ask for them.
```

## Tiers (course mode)

| tier | kind | meaning |
|---|---|---|
| 1 | topic-list | official exam topic list or the professor's exam announcement |
| 2 | professor-notes | review notes, "what to study" messages, announcements that mention the exam |
| 3 | practice-exam | the most recent practice or sample exam |
| 4 | past-exam | earlier real exams |
| 5 | hw · recitation | homework, worksheets, recitation problems |
| 6 | slides · lecture-notes · page | lecture slides, notes, LMS module pages |
| 7 | supplementary | textbook chapters, external explainers |

Auto-tiering when files arrive (LMS pull or `add`): assignments → 5; file name matches practice/past/sample/exam/midterm/final → 3 or 4; module pages and slides → 6; announcements mentioning exam/test/quiz → 2; a page titled topics/syllabus/review → 1 or 2; everything else → 7. Show the tiering once and let the user correct it.

Claim labels for RESOURCES.md and a lesson's `::: sources` drop-down when a fact's authority matters (never inline in STEM lessons): `officially stated`, `professor emphasized`, `repeated in practice`, `inferred`, `out of scope`.

## Rules

- **High-trust only.** Primary sources, recognised experts, peer-reviewed work, well-moderated communities.
- **Annotate every entry.** One line: what it covers and when to reach for it.
- **Course mode uses course material only.** No YouTube, no external explainers, unless the user adds them explicitly.
- **Self-study**: primary sources first; one video from the channel list may be used as a source, its transcript saved under `sources/youtube/` and its entry marked `used-in: NNNN`. Only a used video is embedded in a lesson.
- **Surface gaps.** `## Gaps` lists what is missing; the onboarding ask and `sync` try to fill it.
- **Prune.** Wrong, shallow, or off-mission sources are removed.
