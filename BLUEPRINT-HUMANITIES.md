# Blueprint: humanities exam lesson

For course mode in any subject that is not math, physics, engineering or CS. Like the STEM blueprint it is built from the exam, but it is more conceptual and asks for more recall. One lesson covers one whole exam. Shared rules are in TEMPLATES.md.

## Find the question types

Start from what is graded: past exams, the study guide, essay prompts, quiz questions and the rubric. Group them into **question types**, for example:

- define or identify a term;
- short answer;
- compare two authors or two cases;
- apply a theory to a case;
- essay.

## Size

There is no target length. The size comes from the number of question types and the variations that really appeared. Before writing, tell the user one line with the types, the model answers and the sessions at about 45 minutes each, for example "5 types, 9 model answers, about 4 mornings".

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

Every term, author, date and argument that the questions depend on becomes a flashcard (`::: card`). The front holds the question. The back holds the short answer, and its `must:` lines hold the points it has to contain. Cards are graded on meaning, not wording. The flashcards replace the STEM cheat sheet, and they sit in a `## Flashcards` chapter after the last question type.

## End

1. **Mixed set.** Official questions from all types, shuffled, with no type named.
2. **Practice exam.** One full official-style exam. One line at its top gives the time per question: (total minutes − 10) ÷ number of questions.

## Redo rounds

A study session starts with the cards and questions missed in earlier sessions, then continues with the next new chapter. A later round shows only what was missed. The rounds stop when a round adds no new misses. (Board support is not built yet; see ROADMAP.md.)

## Same as STEM

Official material is quoted verbatim and labelled (TEMPLATES.md **Official problems**). No intros, no previews, no recaps. The size comes from the number of question types, never from a target length.
