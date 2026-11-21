# LMS pull

Turns a pasted course link into tiered files under `$WS/sources/`. The user's logged-in browser is the universal path; a token is the fast path where the LMS allows students to make one.

## Detect

| URL contains | LMS |
|---|---|
| `instructure.com`, `/api/v1/`, `/courses/<id>` on a Canvas host | Canvas |
| `/course/view.php?id=` | Moodle |
| `/ultra/courses/`, `/webapps/` | Blackboard Learn |
| `/d2l/` | Brightspace |
| anything else | unknown → "Drop the files in this folder, or paste the link to a Canvas/Moodle/Blackboard/Brightspace course." |

## Adapters

### Canvas

Fast path: personal token (Account → Settings → New Access Token). Stored in `$WS/.lms-token`. Some schools disable this (Georgia Tech does); then use the browser path.

Endpoints (both paths):

- `GET /api/v1/courses?enrollment_state=active` → pick the course (or take the id from the URL)
- `GET /api/v1/courses/:id/modules?include[]=items&per_page=100`
- `GET /api/v1/courses/:id/files?per_page=100`
- `GET /api/v1/courses/:id/assignments?per_page=100&order_by=due_at`
- `GET /api/v1/courses/:id/pages?per_page=100` then `GET /api/v1/courses/:id/pages/:url`
- `GET /api/v1/announcements?context_codes[]=course_:id&start_date=2000-01-01&per_page=100`
- files: the `url` field of a file object is a signed download link

Browser path: open the school's Canvas host in the user's browser and run `fetch(path, {credentials:'include'}).then(r=>r.json())`. Paginate with `per_page=100` and the `Link: rel="next"` header. With the Claude in Chrome extension keep each result under ~1KB (return only the fields needed, page through them). Download a file by opening its `url` in the tab, then move it from `~/Downloads`.

### Moodle

Fast path: `POST https://<host>/login/token.php` with `username`, `password`, `service=moodle_mobile_app` → `token` (works when the site has the mobile service enabled, most do). Then `https://<host>/webservice/rest/server.php?wstoken=…&moodlewsrestformat=json&wsfunction=core_course_get_contents&courseid=<id>` → sections → modules → `contents[].fileurl` (append `&token=`).

Browser path: the course page lists every resource as `<a href="/mod/resource/view.php?id=…">`; open each and let it download.

### Blackboard Learn

No student self-service keys. Browser path only: `GET /learn/api/public/v1/courses/:courseId/contents?recursive=true` with cookies, then `/learn/api/public/v1/courses/:courseId/contents/:contentId/attachments` and `/attachments/:attachmentId/download`.

### Brightspace

No student keys. Browser path only: `GET /d2l/api/le/1.75/:orgUnitId/content/toc` with cookies, then each topic's `Url` for the file.

## Tag and tier

For each item, set `kind` from where it came from, then tier by RESOURCES-FORMAT.md's table:

| came from | kind | tier |
|---|---|---|
| assignment | hw (assigned: yes) | 5 |
| file whose name matches practice/past/sample/exam/midterm/final | practice-exam / past-exam | 3 / 4 |
| announcement mentioning exam/test/quiz/topics | professor-notes | 2 |
| page titled topics/syllabus/review/study guide | topic-list or professor-notes | 1 / 2 |
| module page, slides (pptx/pdf named lecture/week/slides) | slides / page | 6 |
| everything else | supplementary | 7 |

Extract text next to each file: `pdftotext -layout`, `uv run --with python-pptx python -c …` for pptx, `uv run --with python-docx python -c …` for docx. Save as `<file>.txt` beside the original.

## Layout

```
$WS/sources/
  exams/      practice-test-1.pdf  practice-test-1.pdf.txt
  hw/         hw2.pdf …
  slides/     week2-l2.pdf …
  pages/      module-3-overview.md
  announcements/ 2026-09-01-test1-topics.md
  manifest.json      # {id, kind, tier, title, path, source_url, pulled_at}
```

`manifest.json` lets `sync` pull only new items. After a pull, write the RESOURCES entries and show the tiering once on the board.
