# Interactive lesson blocks

These blocks are local, deterministic, and need no external service. Use one focused question beside each. The renderer accepts JSON data, not executable JavaScript.

## Code execution: `trace`

A verified, precomputed trace; not a compiler. `code` is an array of source lines. Each step shows the state **after** the highlighted 1-based line executes. Use `line: 0` for an initial state. Include cumulative output and a short explanation. Verify the trace against actual execution before publishing. Do not label authored values as runtime measurements.

```text
::: interactive trace
{
  "title": "Watch total change",
  "code": ["int total = 0;", "total += 2;", "System.out.println(total);"],
  "steps": [
    {"line": 0, "variables": {}, "output": "", "note": "Predict total before stepping."},
    {"line": 1, "variables": {"total": 0}, "output": "", "note": "The variable starts at zero."},
    {"line": 2, "variables": {"total": 2}, "output": "", "note": "Adding two changes the stored value."},
    {"line": 3, "variables": {"total": 2}, "output": "2", "note": "Printing reads the value without changing it."}
  ]
}
:::
```

Previous/Next, Play/Pause, and Reset are supplied by the renderer. Playback starts only on request, pauses when the page is hidden, and stops at the final state. Arrays and other values can be represented as JSON in `variables`. A string value is shown as typed, without added quotes, so write the quotes yourself when the variable is a Java String (`"\"hi\""` shows `"hi"`) and leave them off for display text such as `"{1, 2, 3}"` or `"4.0"`. Keep the source short enough to scan; place the lesson's explanation outside the block.

## Polynomial graph: `function`

Coefficients are ordered by ascending power: `[constant, x, x-squared, ...]`. `parameter.index` selects the single coefficient the slider changes. The fixed graph window is x = −5…5, y = −5…5. Choose values whose interesting behavior fits this window. This is a polynomial explorer, not a general expression evaluator.

```text
::: interactive function
{
  "title": "Change the parabola's curvature",
  "coefficients": [0, 0, 1],
  "parameter": {"index": 2, "label": "a", "min": -2, "max": 2, "step": 0.1},
  "prompt": "Move a through zero. Predict when the curve opens upward."
}
:::
```

The range control supports keyboard arrows. For trig functions, changing bounds, geometry, or other unsupported behavior, use an appropriate new implementation or Manim rather than forcing it into this schema.

## Completion check

- The learner changes something relevant and sees its consequence.
- Initial, middle, and final trace states or slider extrema are correct.
- Controls work with keyboard; no autoplay; reset returns to the first trace state.
