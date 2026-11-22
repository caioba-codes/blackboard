# Blueprint: self-study lesson

For self-study, when there is no course and no test. The goal is that the reader enjoys it and comes away able to explain or do something useful. There is no exam, so there is no topics breakdown, no drill, no practice exam and no redo rounds. Shared rules are in TEMPLATES.md.

## Sources

Start from primary sources: official docs, papers and material from the maker. Add one good video (SKILL.md **Sources**). Record all of them in Sources.

## Chapters are questions

Build the lesson from the questions that a curious person would actually ask, in the order that they would ask them. Each chapter title is one such question. For a data center:

1. What is inside the building?
2. Where does the power come from?
3. Why does it need so much water?
4. What happens when you send a prompt?

Cut any question whose answer is neither interesting nor useful. The size comes from the number of questions worth answering.

## Inside a chapter

1. **The answer first.** Answer the question directly in the first lines.
2. **One real example.** Show how it works on one real, specific example, with real numbers and names. Show the actual thing in a photo or a diagram (**Photos** below).
3. **So what.** One short line that connects it to something the reader can use or notice in real life.

Concrete comes before abstract. Use an analogy only to an everyday thing, and only when it is accurate.

## Engagement

Engagement comes from real things, surprising true numbers and good pictures. It never comes from jokes, hype or filler. The readability rules in TEMPLATES.md still apply in full.

## Photos

The banner and the photos matter most here: show the real object (TEMPLATES.md **Photos** for the banner). When a chapter talks about a physical thing and a good photo of it exists, add a `::: photo`:

- one photo of the whole thing, `wide`, in the first chapter;
- a photo of a part, `side`, in the chapter about that part, only if a good photo of that exact part exists;
- `query:` names the object as a photographer would caption it ("NVIDIA DGX Spark desktop computer front");
- two or three photos per lesson is normal, and more than five makes the lesson a gallery.

Abstract topics get `::: fig` drawings, never stock photos.

## End

An optional short quiz of 2 to 3 questions in one `::: quiz` block (QUIZ.md), then `## Extra` with the video that was used. Nothing else.
