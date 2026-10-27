# The board page: how it behaves

Reference for changing `board.html.tmpl` and `bridge.py`. The agent writing lessons does not need it: SKILL.md covers authoring. Describe behavior here when it changes, and keep SKILL.md to what a lesson writer must do.

## Layout and navigation

- **One bridge, every workspace.** `bridge.py` on 7331 serves every course. Each workspace has a slug (the directory above `learn`) and its own current lesson; `render.sh` pins the board tab to `/w/<slug>/`, so two sessions rendering different courses never clobber each other. `/lessons` is the hub across every folder (search, folder chips, Recent, this folder, other folders on this computer). `/w/<slug>/lessons/NNNN#e3` links to a lesson and a note, `#s-<heading-slug>` to a section.
- **Top bar.** Left: an **All lessons** link and the zoom control (− 100% +, keys `-` `+` `0`, 70% to 200% of the lesson column, remembered in this browser). Center: full-text search over every lesson in every folder (`/api/search`), showing the matching line with the words highlighted and its section, opening the lesson scrolled there (key `/`, arrows and Enter). The hub's search box uses the same search. Right: the XP health bar and the chat button.
- **XP health bar.** One segment per quiz item, in the lesson's accent (gold when full). XP counts verified answers only (multiple choice right, flashcards graded 4 or 5). The bar is the Contents button: click it or press `t` to open the **level map**, a card that drops from under the button on the left (so it sits beside the docked chat): each chapter is a square node on one dashed path (cleared = filled accent, current = chalk with a pulsing glow and YOU ARE HERE, not started = dim outline; nothing is locked), its checkpoint score as stars (★★, ★☆), the current chapter's `###` sections as small sub-nodes, and the path filled up to the reading position. A Practice Exam chapter is the BOSS tile, a Cheat Sheet chapter the SAVE POINT, the Quiz the final node. Every node is a link, with its state in its accessible name.
- **Chapters only.** The right-edge reading scale (its ticks and hover labels) and the level map list only the lesson's `## Chapter N · …` headings (the cheat-sheet chapter included) and `## Quiz`; the topics breakdown, Sources and any other `##` stay out. A lesson with no `Chapter` headings keeps every `##`.
- **Reading scale.** Down the right edge, a ruler in the lesson's accent: one mark per `##` at its heading's true place, beside a thin bar filled to the reading position. It measures reading position only, never mastery or XP. Hover shows the title, click jumps. On lesson pages the system scrollbar is hidden and the scale is the scrollbar (drag or click it). A page that fits on screen is full. The hub has no scale.
- **Headings.** `###` subtitles are underlined; bold `**Step N · …**` lead-ins at the start of a paragraph are boxed with a hand-drawn chalk stroke in the accent.
- **Workspaces** are every folder ever rendered plus everything found by scanning the roots in `~/.cache/blackboard/config.json` (`{"scan": ["~/notes", "~/school"]}`; `BLACKBOARD_SCAN=a:b` overrides) for `lessons/` folders.

## Writing animation and sounds

- **Chalk writing.** New blocks arriving through SSE are written with one pen, top to bottom: words letter by letter with a chalk edge, display math swept left to right without splitting KaTeX glyphs, `###` underlines, `**Step N**` boxes and diagram strokes drawn in turn. Opening a lesson shows what is already there at once; only content that lands afterwards is written. Interactive blocks reveal their title, and their controls stay immediately usable. No flashing frames, cursors or forced scroll. There is no loading bar: before the body the brainstorm notes, between blocks a resting chalk stick.
- **Reduce Motion.** The chalk writing and the quiz celebration play even with Reduce Motion on, because Caio asked for them: both are short and never loop. Other transitions (drawer, chat, focus rings) honor Reduce Motion.
- **Quiz celebration.** A right pick plays gold 8-bit pixel sparks, a floating `+1 XP`, a combo counter for consecutive right picks and a square-wave chime; every item right plays a `QUIZ CLEARED` fanfare.
- **Cues** in the same 8-bit voice: a power-on arpeggio when a lesson starts streaming, a blip per new `##` while it streams, a stage-clear jingle when it finishes, an item-get chime when an Explain note arrives, a soft low thud on a wrong pick, a chime or thud when a flashcard is graded. Key `m` mutes all of it, remembered per browser.

## Quiz behavior

- Multiple-choice answers stay changeable: another pick replaces the verdict, and the key is revealed only once picked. A wrong pick shows "Not quite"; the `why:` line appears once the right option is picked.
- Once answered, a quiet **↺ Reset** under the item (keyboard-accessible) clears the pick, verdict and revealed key and takes back that item's XP segment and the combo.
- Every click logs to `learning-records/quiz-log.jsonl` (`mode: mcq`, score 5 or 0); a Reset appends `{mode: "mcq", item, event: "reset"}`. The latest event per item is restored on reload, and a restored pick counts for XP.
- Flashcard deck, Speak and grading: QUIZ.md.

## Selecting text

- Selecting inside a display equation works like text: a drag across lines selects whole visual lines (Explain receives those rows as TeX); a drag on one line selects just the symbols it covers, going inside a fraction or power when the drag sits inside it (Explain receives e.g. `x^2 (in $x^{2}-x=0$)`). Inline math lights up as a whole formula.
- The selection raises **Explain**, **Definition** (1–5 words only) and **Ask** (opens the chat with the selection quoted).

## Explain callouts

A full-width block below the selected paragraph, framed like chalk: a hand-drawn border (uneven radii) in the accent over a dark translucent fill, a lightbulb and a title in accent chalk, ivory body text, a visible toggle. New callouts open automatically; folding hides only the body, and the whole header stays clickable and keyboard-operable. Clicking or selecting the body does not collapse it. A discreet × removes the block. Loading and error messages show inside the same callout. Writing, folding or removing a callout rewrites the lesson file and rebuilds the page; the rebuild keeps the first visible block at the same screen position, and `#s-…`/`#e…` deep links apply only on the first load. Old `deep` notes render the same way, and old `==…==` markers render as plain text.

## Definition

A one-sentence meaning of the selected term as this lesson uses it, in a small popup at the selection. It closes on an outside click, Escape or scroll; the selected term keeps a dotted underline that reopens it (Enter/Space too). Anchors persist per workspace and lesson in this browser. Nothing is written to the lesson file and nothing reaches the chat. `POST /define` answers through `bin/define.py`, cheapest source first:

1. **The lesson's own words**: a table row, a `**Term** — …` note, a `Term:` line, or a `GLOSSARY.md` entry, returned verbatim (`via: lesson`).
2. **Precompute**: serving a lesson starts a background pass over its own terms (emphasis used more than once, table keys, inline code, words already asked about; 40 max), one at a time and yielding to real clicks, only when a local model is installed.
3. **Disk cache**: `~/.cache/blackboard/defs/<slug>/<lesson>.json`. Delete it to regenerate.
4. **Local model**: Ollama. `BLACKBOARD_DEFINE_LOCAL` picks the model; by default a plain instruct model (`llama3.2:3b`, `gemma3`), else the smallest installed. Avoid hybrid reasoning models: on Ollama 0.33 neither `think: false` nor `/no_think` silences qwen3. The bridge keeps it warm (`keep_alive` 30 m, a one-token ping at startup and on each page view).

`claude -p` (`BLACKBOARD_DEFINE_MODEL`, default Haiku) is the fallback when Ollama is not running: correct, but 12–20 s. Measured on a K-map lesson: 0.00 s for a term the lesson defines or precompute covered, 0.7 s otherwise, 0.01 s for a repeat after a bridge restart. The definer gets the selected block, the lines around it, other lines using the term, and the lesson title and course. Output is normalized (a leading "A <term> is …" trimmed, `$…$`-wrapped prose unwrapped, a scratchpad opener triggers one stricter retry). Answers are cached per lesson and term, hovering prefetches, and concurrent requests for a term share one result.

## Chat panel

Docks on the right of every lesson page. A round button in the top bar and ⌘⇧. (Ctrl+Shift+. elsewhere) open and close it; the open state carries across lessons and the lesson column moves left. Each lesson has its own Claude Code session, run by `bridge.py` as `claude -p` in the workspace and resumed every turn, with history in `$WS/reference/chat/NNNN.json`; **+** archives that file as `NNNN-<time>.json` and starts fresh. Every turn names the lesson being read and lists its sources (`## Sources` and `RESOURCES.md`, resolved to files and URLs). Tool steps show live and fold away when the reply ends; the square button stops a reply; a reply keeps running and is saved if the page goes away. Model: `BLACKBOARD_CHAT_MODEL` (default `opus`) at medium effort. It may read only the workspace, TEMPLATES.md and the files the lesson cites, fetch only the sites the lesson cites, and search the web; edits only inside the workspace; anything else is denied without a prompt. Instructions: `chat-system.md`. It does not load the user's CLAUDE.md, hooks or MCP servers, and only the board's own pages may call it.

## Source viewer

Every file a lesson cites opens over the lesson column, with the chat still docked on the right. The Sources drop-down links its own relative links and adds **Files used**, grouped by folder: the files in the sources block plus each problem's `<!-- source: … -->` comment (with its first page); a solution file (`…-s2`) brings its exam (`…-e2`). File paths the chat cites (`exams2/fa18-kj-s2.pdf`, page 1) become the same links. PDFs open in the browser's viewer at the page, images fit the width, text and Markdown render in place; the bar has the file name, **Open in new tab** and **Back to lesson** (Esc), and closing restores the scroll position. While a file is open, each chat turn carries `[Viewing: <path>, page N]`, so "this problem" means that file.

`/api/sources?id=NNNN` lists the files, `/api/source-check?p=…` checks chat citations, and `/source/<path>` serves one. `source_file` looks in `sources/`, the workspace, `lessons/` and the course folder, and serves a file only when its real path is inside the course folder, outside hidden folders, with a pdf, image, txt, md, csv or tex extension (no svg or html); extracted text (`x.pdf.txt`) opens the PDF. Other web pages get 403. Missing files show "not found on this Mac"; nothing is copied.

## End card

Every lesson except `plain: true` boards ends with a card: Ultraman Mebius beside a quote of his battle sounds (one of ~30 in `ENDCARD_QUOTES`, picked by workspace slug + lesson id, so a lesson always shows the same one), and a **Color timer** button that plays an 8-bit "ning nung" loop (click only, `m` mutes it). It stays out of the rail, contents map, search, Explain/Definition and XP, and hides while a lesson is streaming. The Kindle EPUB gets it as its last page.

The photo is local and never part of the skill: `bridge.py` serves `/end-card.jpg` from `BLACKBOARD_END_CARD`, else `"end_card"` in `~/.cache/blackboard/config.json` (`{"end_card": "~/Pictures/mebius.jpg"}`), else `~/.config/blackboard/end-card.jpg`, and refuses a path inside the skill folder. With no photo the card shows the quote alone. Never commit the image: it is someone else's copyright.

## Slate surface

`board: slate` in front matter gives a real-blackboard surface: `slate.jpg` ("Black smooth textured paper background" from magnific.com, Freepik free license: credit it when the skill is shared publicly), stacked on its mirror so it tiles and scrolls with the text, with a faint chalk bloom and grain (`chalk.png`) on text, math and diagrams. A `slate-custom.jpg` next to it replaces the photo. On trial; it may become the default.

Credit: board surface photo by Freepik via magnific.com.
