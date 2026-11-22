# Figures

A figure is a `::: fig <template>` block whose body is one JSON object. The board draws it as inline SVG on a 720-wide canvas: chalk-white strokes with a hand-drawn wobble (Rough.js), `Patrick Hand` for figure text, the accent `#9b3a4a` only for what changed. Check it first:

```
bin/fig.mjs --list                                  # templates
bin/fig-check.sh taccounts spec.json bank            # renders → prints a PNG path; look at it
```

Lint warnings (overlapping labels, text outside the canvas, a bar too thin for its label) print to stderr and show under the figure on the board until fixed.

Common keys: `caption` (markdown, shown under the figure: a short description only, never the explanation; see TEMPLATES.md **Photos**), `unit` (`"$"` default, `""` for plain numbers, `"€"`…), `seed` (re-roll the wobble), `hi` (what to draw in the accent colour).

## When to illustrate

Add a diagram whenever it makes an explanation easier to picture or understand than prose alone, in a worked example, a comparison or an explanation. The trigger is teaching value, not the first mention of a term, and one visual somewhere in the lesson is not enough when another step needs one. Typical cases: a balance sheet, a flow of money, a timeline, a K-map, vectors, a waveform, a small graph.

- Place it beside the step it explains; labels on the figure, not in prose. The caption in the spec only names the figure.
- Name the same parts in prose and drawing. Distinguish control signals from conducting paths, mark connection points and gaps, label simplified models, and show contrasting states when that explains what changes.
- Keep it on the causal path: 7 elements or fewer, labels beside the thing they name, one highlight colour on what changed, no legend.
- Prefer a schematic for relationships and a real photo for physical appearance (TEMPLATES.md **Photos**).
- Before it lands, run `bin/fig-check.sh <template> <spec.json>` and look at the PNG: fix overlaps and cut anything off the path.

## taccounts — one or more T-accounts, before → after

```json
{"panels":[{"title":"Before the loan","left":[["Cash",110]],"right":[["Deposits",100],["Owners",10]]},
           {"title":"After the loan","left":[["Cash",110],["Loan",80]],"right":[["Deposits",180],["Owners",10]],"hi":["Loan","Deposits"]}],
 "arrow":"+$80 both sides","heads":["owns / is owed","owes"],"caption":"…"}
```
`totals:false` on a panel hides the sums. Up to three panels.

## bars — stacked balance-sheet bars (Bank of England style), equal-height sides

```json
{"panels":[{"title":"Before","left":[["Cash",110]],"right":[["Deposits",100],["Equity",10]]},
           {"title":"After","left":[["Cash",110],["Loan",80,true]],"right":[["Deposits",180,true],["Equity",10]]}],
 "heads":["assets","liabilities + equity"]}
```
Third element `true` marks a new segment (accent outline + hatch). Segments under ~22 px get no label; say it in the caption.

## flow — entities and labelled arrows

```json
{"nodes":[{"id":"s","label":"Saver","col":0},{"id":"b","label":"Bank","col":1,"hi":true},{"id":"r","label":"Baker","col":2}],
 "edges":[{"from":"s","to":"b","label":"$100 deposit"},{"from":"b","to":"r","label":"$80 loan","hi":true},{"from":"r","to":"b","label":"6 % a year","side":"below"}]}
```
`col`/`row` place nodes on a grid (omit both for one row). `shape:"circle"` for a node. Keep it to ~6 nodes; beyond that use D2 and inline the SVG.

## timeline

```json
{"events":[{"at":0,"label":"loan made"},{"at":6,"label":"first payment"},{"at":12,"label":"repaid","hi":true}],"unit":"months"}
```
Numeric `at` places to scale; without numbers events are evenly spaced.

## table

```json
{"cols":["","loan rate","deposit rate","spread"],"rows":[["2024","6 %","1 %","5 %"],["2025","5 %","2 %","3 %"]],"align":["l","r","r","r"],"hi":[[1,3]]}
```
`hi` is `[row, col]` pairs; `[row]` alone highlights the row.

## kmap — Karnaugh map, values by minterm index

```json
{"vars":["A","B","C","D"],"values":[0,1,1,0, 0,1,1,0, 0,0,0,0, 0,0,0,0],"loops":[{"cells":[1,5],"label":"A̅ C̅ D"},{"cells":[2,6],"label":"A̅ C D̅"}]}
```
Rows are the first variables in Gray order, columns the rest. A loop is the bounding box of its cells: split a loop that wraps an edge into two.

## vectors

```json
{"range":[-1,5],"vectors":[{"x":3,"y":1,"label":"u"},{"x":1,"y":3,"label":"v"},{"x":4,"y":4,"label":"u + v","hi":true}]}
```
`from:[x,y]` starts a vector elsewhere than the origin.

## wave — function plot or sampled points

```json
{"x":[0,6.283],"y":[-1.2,1.2],"series":[{"expr":"sin(x)","label":"sin"},{"expr":"sin(2*x)/2","label":"half","hi":true}],"marks":[{"x":3.1416,"label":"π"}],"xlabel":"t","ylabel":"v"}
```
`expr` is a JavaScript expression in `x` with `Math` in scope; or give `points:[[x,y],…]`.

## raw — anything else, on the 720-wide canvas

```json
{"h":200,"items":[{"t":"rect","x":40,"y":30,"w":160,"h":60},{"t":"text","x":120,"y":66,"text":"bank","anchor":"middle"},
 {"t":"arrow","x1":200,"y1":60,"x2":320,"y2":60,"hi":true},{"t":"circle","x":380,"y":60,"r":30},{"t":"curve","points":[[420,150],[500,90],[600,160]]}]}
```
Item types: `line x1 y1 x2 y2`, `rect x y w h`, `circle x y r`, `arrow x1 y1 x2 y2`, `poly points`, `curve points`, `path d`, `text x y text [anchor size weight italic]`. Any item takes `hi:true`, `color`, `width`, `fill`.

## Rules

1. One idea per figure, at most 7 elements. Split rather than crowd.
2. Labels beside the thing they name. No legend.
3. One highlight: what changed, in the accent. Everything else chalk.
4. Before → after reads left to right. Equal sides have equal heights.
5. Figure width is the text column. No frame, no decoration.
6. Numbers in the figure are the lesson's numbers.
7. Look at the PNG from `bin/fig-check.sh` before placing the block.
