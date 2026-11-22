# Blueprint: humanities exam lesson

For course mode in any subject that is not math, physics, engineering or CS. Like the STEM blueprint it is built from the exam, but it is more conceptual and asks for more recall. One lesson covers one whole exam. Shared rules are in TEMPLATES.md.

## Find the question types

Start from what is graded: past exams, the study guide, essay prompts, quiz questions and the rubric. Group them into **question types**, for example:

- define or identify a term;
- short answer;
- compare two authors or two cases;
- apply a theory to a case;
- essay.

**Question sources, best first.** Past exams of this test; the study guide or official review; past exams of the earlier tests in this course; the student's own graded work; assignments and essay prompts; lecture questions. Use the best that exist and say in Sources which were used and when no past exam of this test exists. For a cumulative final, the types are those of the earlier tests plus the new material's; weights come from the syllabus or instructor, otherwise an estimate printed as one under the breakdown. Types an earlier lesson taught get one model answer and one Your turn. A type with no official question gets questions in the format of the nearest official ones, labelled "Written by Claude", one model answer and one Your turn, and Sources says so.

## Size

There is no target length. The size comes from the number of question types and the variations that really appeared. Before writing, tell the user one line with the types, the model answers and the number of sessions, for example "5 types, 9 model answers, about 4 mornings". A session is the length the user stated, most recent first, then MISSION.md or NOTES.md; 45 minutes when none is stated.

## Top of the lesson

Contents, then Sources, then a breakdown of the graded work by question type: the percent of the grade for each type, averaged over the past exams, in the same table format as the STEM **Exam Topics Breakdown**.

## One chapter per question type

Chapters go in order of weight, the biggest first. A chapter is one study session. It stands on its own and never depends on reading another chapter the same day.

Inside a chapter, in this order:

1. **The question.** One official question, verbatim, with its label, in a `::: given` block.
2. **What it asks.** In plain words, and what a full-credit answer must contain. Take this from the rubric when one exists.
3. **What you need.** Only the ideas this question uses. Each concept, author or argument is one claim, the reason for it, and one concrete example from the course material.
4. **Model answer.** A full answer with its parts labelled: claim, reason, evidence, term defined.
5. **Your turn.** Another official question. The student answers from memory, and the model answer sits behind the reveal.
6. **Variations.** Each variation that really appeared on a past exam: what is different, a model answer, and a Your turn.

## Recall

Every term, author, date and argument that the questions depend on becomes a flashcard (`::: card`). The front holds the question. The back holds the short answer, and its `must:` lines hold the points it has to contain. Cards are graded on meaning, not wording. The flashcards replace the STEM cheat sheet. They sit in one `::: quiz` block (so they form one deck) in a `## Chapter N · Flashcards` chapter after the last question type.

## End

1. **Mixed set.** Official questions from all types, shuffled, with no type named.
2. **Practice exam.** One full official-style exam. One line at its top gives the time per question: (total minutes − 10) ÷ number of questions. With no official exam, assemble it from official questions in the proportions of the breakdown and label it "Assembled from official questions"; never present it as a real past exam.

## Redo rounds

Check-in answers end with **Got it** and **Missed it**, and a wrong multiple-choice pick counts as missed. While a lesson has misses, a row under its title reads "N missed problems · Redo them". A study session starts there: Redo them shows only the missed questions, then the session continues with the next new chapter. A Got it drops a question from the next round; **Next round** shows what is still missed. The rounds stop at "No misses left." Flashcards are not part of a round.

## Same as STEM

Official material is quoted verbatim and labelled (TEMPLATES.md **Problems and solutions**). No intros, no previews, no recaps. The size comes from the number of question types, never from a target length.
