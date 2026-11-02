---
title: How to Ace Your Second Integral Calculus Test
course: Integral Calculus
exam: Second test
model: Claude Fable 5.1 High
image: calculus integrals handwritten in a notebook
photo: assets/0001-3d41ade1287038cf.jpg
credit: Cornell University notebook and exam pages for Math 221, Spring 1973 · Jonathan Schilling (CC BY-SA 4.0, Wikimedia Commons)
photo_source: https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b1/Cornell_University_notebook_and_exam_pages_for_Math_221%2C_Spring_1973.jpg/1920px-Cornell_University_notebook_and_exam_pages_for_Math_221%2C_Spring_1973.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail
---

# How to Ace Your Second Integral Calculus Test

::: prerequisites
- The basic antiderivative table (the twelve rows and the four log rows)
- u-substitution: pick $u$, compute $du$, no $x$ left on the $u$ line
- Definite integrals: bracket, upper minus lower, no $+C$
- Integration by parts once: $\int u\,dv = uv - \int v\,du$
- Derivatives of $\sin$, $\cos$, $\tan$, $\sec$, $e^{x}$, $\ln x$, $\tan^{-1}x$
- Unit-circle values at $0$, $\pi/6$, $\pi/4$, $\pi/3$, $\pi/2$
:::

::: contents
1. [Chapter 1 · Integration by Parts](#s-chapter-1-integration-by-parts) · LIATE, the table method, the loop, definite form.
2. [Chapter 2 · Trig Integrals](#s-chapter-2-trig-integrals) · the six identities and the four cases for powers of trig.
3. [Chapter 3 · Trig Substitution](#s-chapter-3-trig-substitution) · the three forms, the triangle, getting back to $x$.
4. [Chapter 4 · Partial Fractions](#s-chapter-4-partial-fractions) · long division first, linear, repeated, irreducible quadratic.
5. [Chapter 5 · L'Hôpital's Rule](#s-chapter-5-l-hopital-s-rule) · the seven indeterminate forms, and checking the form first.
6. [Chapter 6 · Improper Integrals](#s-chapter-6-improper-integrals) · both types, the limit notation graders want, p-integrals, comparison.
7. [Chapter 7 · Which Technique](#s-chapter-7-which-technique) · integrand shape to method, with nine mixed drills.
8. [Chapter 8 · Practice Exam](#s-chapter-8-practice-exam) · a full mock test, answers hidden.
9. [Chapter 9 · Last Night Cheat Sheet](#s-chapter-9-last-night-cheat-sheet) · one screen of formulas.
:::

::: sources
- OpenStax Calculus Volume 2, chapter 3 · integration by parts, trig integrals, trig substitution, partial fractions, improper integrals
- OpenStax Calculus Volume 1, section 4.8 · L'Hôpital's rule and the indeterminate forms
- Banner photo · Jonathan Schilling, Wikimedia Commons (CC BY-SA 4.0)
- Every worked example, drill and practice problem here is original to this lesson, labeled "Written by Claude"
:::

## Exam Topics Breakdown

| Section | % of exam | Shape it takes |
|---|---:|---|
| Improper integrals | 25% | evaluate $\int_a^{\infty}$ (needs parts or a $u$ inside) · "for what $p$" |
| Trig substitution | 22% | a root or a $3/2$ power of $a^{2} \pm x^{2}$ or $x^{2} - a^{2}$ |
| Partial fractions | 22% | linear, repeated or irreducible factors · a definite one with two linear factors |
| Integration by parts | 13% | $\int x\sec^{2}(kx)$, $\int x e^{kx}$, $\int x^{n}\ln x$ |
| Trig integrals | 13% | one odd power to save · both powers even |
| L'Hôpital's rule | 5% | one limit; check the form first |

Illustrative weights; build this table from your own past exams.

::: callout
wrong: $1/\infty = 0$
right: $\displaystyle\lim_{x\to\infty}\frac{1}{x} = 0$
$\infty$ is not a number.
:::

## Chapter 1 · Integration by Parts

### The tool

Use integration by parts when the integrand is a product of two factors that no substitution handles. Split it into $u$ and $dv$, and the formula trades the integral for $uv$ minus $\int v\,du$.

::: key
$$\int u\,dv = uv - \int v\,du$$
:::

$u$ is the piece you differentiate; $dv$ is the piece you integrate.

### Pick $u$ with LIATE

Pick as $u$ the factor whose type comes first in LIATE; the other factor, with $dx$, is $dv$.

::: big
$$\underset{\text{Log}}{\mathrm{L}}\qquad\underset{\text{Inverse trig}}{\mathrm{I}}\qquad\underset{\text{Algebraic}}{\mathrm{A}}\qquad\underset{\text{Trig}}{\mathrm{T}}\qquad\underset{\text{Exponential}}{\mathrm{E}}$$
:::

$$\int \underbrace{2x}_{\textbf{A}\text{lgebraic}}\;\underbrace{\sec^{2}(4x)}_{\textbf{T}\text{rig}}\,dx$$

A comes before T, so $u = 2x$ and the rest is $dv$.

### Worked example: $\int 2x\sec^{2}(4x)\,dx$

Set up the box first: differentiate $u$ to get $du$, and integrate $dv$ to get $v$. Then put the four pieces into $uv - \int v\,du$.

$$\boxed{\begin{aligned} u &= 2x & dv &= \sec^{2}(4x)\,dx \\ du &= \why{2\,dx}{\tfrac{d}{dx}(kx) = k} & v &= \why{\tfrac{1}{4}\tan(4x)}{\int\sec^{2}(ax)\,dx = \tfrac{1}{a}\tan(ax) + C} \end{aligned}}$$

$$\begin{aligned}
\int 2x\sec^{2}(4x)\,dx &= \frac{x}{2}\tan(4x) - \int \frac{1}{4}\tan(4x)\cdot 2\,dx &&uv - \int v\,du \\
&= \frac{x}{2}\tan(4x) - \frac{1}{2}\int \tan(4x)\,dx &&\text{constants out} \\
&= \frac{x}{2}\tan(4x) - \frac{1}{2}\cdot\frac{1}{4}\ln\lvert\sec(4x)\rvert + C &&\int\tan(ax)\,dx = \tfrac{1}{a}\ln\lvert\sec(ax)\rvert \\
&= \boxed{\frac{x}{2}\tan(4x) - \frac{1}{8}\ln\lvert\sec(4x)\rvert + C} &&\text{multiply the constants}
\end{aligned}$$

::: checkin
- *Written by Claude* Your turn: $\displaystyle\int x e^{5x}\,dx$  ||  A comes before E, so $u = x$.

  $$\boxed{\begin{aligned} u &= x & dv &= e^{5x}\,dx \\ du &= \why{dx}{\tfrac{d}{dx}x = 1} & v &= \why{\tfrac{1}{5}e^{5x}}{\int e^{ax}\,dx = \tfrac{1}{a}e^{ax} + C} \end{aligned}}$$

  $$\begin{aligned}
  \int x e^{5x}\,dx &= \tfrac{x}{5}e^{5x} - \int \tfrac{1}{5}e^{5x}\,dx &&uv - \int v\,du \\
  &= \boxed{\tfrac{x}{5}e^{5x} - \tfrac{1}{25}e^{5x} + C} &&\int e^{ax}\,dx = \tfrac{1}{a}e^{ax}
  \end{aligned}$$
:::

### Repeated parts: the table

When $u$ is a polynomial, pick $u$ by LIATE and make a table: the $u$ column holds its derivatives, the $dv$ column holds the antiderivatives of $dv$. Differentiate $u$ until you hit $0$, fill the $dv$ column down to the same row, and the table is complete.

$$\int (x^{2}-x)e^{2x}\,dx$$

| sign | $u$: differentiate down to $0$ | $dv$: integrate down |
|---|---|---|
| $+$ | $x^{2}-x$ | $e^{2x}$ |
| $-$ | $\why{2x-1}{\tfrac{d}{dx}x^{n} = nx^{n-1}}$ | $\why{\tfrac{1}{2}e^{2x}}{\int e^{ax}\,dx = \tfrac{1}{a}e^{ax} + C}$ |
| $+$ | $2$ | $\tfrac{1}{4}e^{2x}$ |
| | $0$ | $\tfrac{1}{8}e^{2x}$ |

Multiply each $u$ entry by the $dv$ entry one row down, with signs $+,-,+$.

$$\begin{aligned}
\int (x^{2}-x)e^{2x}\,dx &= (x^{2}-x)\cdot\tfrac{1}{2}e^{2x} - (2x-1)\cdot\tfrac{1}{4}e^{2x} + 2\cdot\tfrac{1}{8}e^{2x} + C &&\text{diagonals with signs } +,-,+ \\
&= \tfrac{1}{2}(x^{2}-x)e^{2x} - \tfrac{1}{4}(2x-1)e^{2x} + \tfrac{1}{4}e^{2x} + C &&\text{simplify each constant} \\
&= \tfrac{1}{2}(x^{2}-2x+1)e^{2x} + C &&\text{collect: } \tfrac{1}{2}x^{2} - x + \tfrac{1}{2} \\
&= \boxed{\tfrac{1}{2}(x-1)^{2}e^{2x} + C} &&\text{perfect square}
\end{aligned}$$

### The loop: $e^{x}$ times $\sin x$ or $\cos x$

Here the table doesn't work, because neither factor ever differentiates to $0$. Call the integral you start with $I$: after two rounds of parts, $I$ shows up again on the right side, so move it to the left and solve for $I$.

Round 1, with $u$ trig:

$$\boxed{\begin{aligned} u &= \sin x & dv &= e^{x}\,dx \\ du &= \why{\cos x\,dx}{\tfrac{d}{dx}\sin x = \cos x} & v &= \why{e^{x}}{\int e^{x}\,dx = e^{x} + C} \end{aligned}}$$

$$\begin{aligned}
I &= \int e^{x}\sin x\,dx \\
&= e^{x}\sin x - \int e^{x}\cos x\,dx &&uv - \int v\,du
\end{aligned}$$

Round 2, with $u$ trig again:

$$\boxed{\begin{aligned} u &= \cos x & dv &= e^{x}\,dx \\ du &= \why{-\sin x\,dx}{\tfrac{d}{dx}\cos x = -\sin x} & v &= e^{x} \end{aligned}}$$

$$\begin{aligned}
\int e^{x}\cos x\,dx &= e^{x}\cos x - \int e^{x}(-\sin x)\,dx &&uv - \int v\,du \\
&= e^{x}\cos x + I &&\text{the original integral is back}
\end{aligned}$$

$$\begin{aligned}
I &= e^{x}\sin x - \left(e^{x}\cos x + I\right) &&\text{round 2 into round 1} \\
I &= e^{x}\sin x - e^{x}\cos x - I &&\text{distribute the minus} \\
2I &= e^{x}\sin x - e^{x}\cos x &&\text{move } I \text{ to the left} \\
I &= \boxed{\tfrac{1}{2}e^{x}(\sin x - \cos x) + C} &&\text{divide by 2, add } C
\end{aligned}$$

### Definite integrals by parts

Bracket the $uv$ term between the limits; no $+C$.

$$\begin{aligned}
\int_{1}^{e}\ln x\,dx &= \Big[x\ln x\Big]_{1}^{e} - \int_{1}^{e} x\cdot\frac{1}{x}\,dx &&u = \ln x,\ dv = dx,\ du = \why{\tfrac{dx}{x}}{\tfrac{d}{dx}\ln x = \tfrac{1}{x}},\ v = x \\
&= \Big[x\ln x\Big]_{1}^{e} - \int_{1}^{e} 1\,dx &&\text{cancel } x \\
&= (e\ln e - 1\ln 1) - (e - 1) &&\text{upper minus lower, twice} \\
&= (e - 0) - e + 1 &&\ln e = 1,\ \ln 1 = 0 \\
&= \boxed{1}
\end{aligned}$$

### Checkpoint

*Written by Claude*

::: mcq c1a b
$\displaystyle\int x e^{x/2}\,dx$ equals which of these?
- $2xe^{x/2} + 4e^{x/2} + C$ || The minus in $uv - \int v\,du$ was dropped.
- $2xe^{x/2} - 4e^{x/2} + C$
- $x^{2}e^{x/2} + C$ || This integrates the two factors separately; the integral of a product is not the product of integrals.
- $2xe^{x/2} - 2e^{x/2} + C$ || The second integral lost its $2$: $\int e^{x/2}\,dx = 2e^{x/2}$.
why: A comes before E, so $u = x$. $$\boxed{\begin{aligned} u &= x & dv &= e^{x/2}\,dx \\ du &= dx & v &= \why{2e^{x/2}}{\int e^{ax}\,dx = \tfrac{1}{a}e^{ax} + C} \end{aligned}}$$ $$\begin{aligned} \int x e^{x/2}\,dx &= 2xe^{x/2} - \int 2e^{x/2}\,dx &&uv - \int v\,du \\ &= \boxed{2xe^{x/2} - 4e^{x/2} + C} &&\int e^{ax}\,dx = \tfrac{1}{a}e^{ax},\ a = \tfrac{1}{2} \end{aligned}$$
:::

*Written by Claude*

::: mcq c1b c
$\displaystyle\int x^{3}\ln x\,dx$ equals which of these?
- $\tfrac{x^{4}}{4}\ln x - \tfrac{x^{3}}{4} + C$ || The last $\tfrac{1}{4}\int x^{3}\,dx$ was left as $\tfrac{1}{4}x^{3}$; it still needs the power rule.
- $\tfrac{x^{4}}{4}\ln x + \tfrac{x^{4}}{16} + C$ || The minus in $uv - \int v\,du$ was dropped.
- $\tfrac{x^{4}}{4}\ln x - \tfrac{x^{4}}{16} + C$
- $4x^{4}\ln x - x^{4} + C$ || $v$ was taken as $4x^{4}$; the power rule divides by $4$, so $v = \tfrac{x^{4}}{4}$.
why: L comes before A, so $u = \ln x$. $$\boxed{\begin{aligned} u &= \ln x & dv &= x^{3}\,dx \\ du &= \why{\tfrac{1}{x}\,dx}{\tfrac{d}{dx}\ln x = \tfrac{1}{x}} & v &= \why{\tfrac{x^{4}}{4}}{\int x^{n}\,dx = \tfrac{x^{n+1}}{n+1} + C} \end{aligned}}$$ $$\begin{aligned} \int x^{3}\ln x\,dx &= \tfrac{x^{4}}{4}\ln x - \int \tfrac{x^{4}}{4}\cdot\tfrac{1}{x}\,dx &&uv - \int v\,du \\ &= \tfrac{x^{4}}{4}\ln x - \tfrac{1}{4}\int x^{3}\,dx &&\tfrac{x^{4}}{x} = x^{3} \\ &= \boxed{\tfrac{x^{4}}{4}\ln x - \tfrac{x^{4}}{16} + C} &&\text{power rule} \end{aligned}$$
:::

## Chapter 2 · Trig Integrals

### The six identities

Every trig integral here is rewritten with one of these until a $u$-substitution appears. Memorize them.

| name | identity | what it is for |
|---|---|---|
| Pythagorean | $\sin^{2}x + \cos^{2}x = 1$ | trade $\sin^{2}$ for $\cos^{2}$ or back |
| Pythagorean | $1 + \tan^{2}x = \sec^{2}x$ | trade $\tan^{2}$ for $\sec^{2}$ or back |
| Pythagorean | $1 + \cot^{2}x = \csc^{2}x$ | trade $\cot^{2}$ for $\csc^{2}$ or back |
| power reducing | $\sin^{2}x = \tfrac{1}{2}(1 - \cos 2x)$ | an even power with nothing to save |
| power reducing | $\cos^{2}x = \tfrac{1}{2}(1 + \cos 2x)$ | an even power with nothing to save |
| double angle | $\sin 2x = 2\sin x\cos x$ | $\sin x\cos x$ as one function |

### The four cases: what to save as $du$

For a product of powers of sine and cosine, or of tangent and secant, find the row that matches the powers. Save the factor in the second column as $du$, and rewrite everything else in terms of $u$.

::: big
| Integrand | Save as $du$ | Rewrite the rest | $u$ |
|---|---|---|---|
| $\sin^{m}x\cos^{n}x$, one power odd | one factor of the odd one | $\sin^{2} = 1 - \cos^{2}$ | the other function |
| $\sin^{m}x\cos^{n}x$, both even | nothing | power reducing | none |
| $\tan^{m}x\sec^{n}x$, $n$ even | $\sec^{2}x$ | $\sec^{2} = 1 + \tan^{2}$ | $\tan x$ |
| $\tan^{m}x\sec^{n}x$, $m$ odd | $\sec x\tan x$ | $\tan^{2} = \sec^{2} - 1$ | $\sec x$ |
:::

The saved factor is always $du$ for the $u$ in the last column. Cotangent and cosecant follow the last two rows with a minus sign, because of these derivatives.

$$\begin{aligned} (\cot x)' &= -\csc^{2}x \\ (\csc x)' &= -\csc x\cot x \end{aligned}$$

### Case 1: one power odd

When sine or cosine has an odd power, save one factor of the odd one as $du$. Turn the even power left over into the other function with $\sin^{2}x + \cos^{2}x = 1$, and substitute.

$$\int \underbrace{\sin^{6}x}_{\text{even}}\;\underbrace{\cos^{3}x}_{\text{odd: save one}}\,dx$$

$$\begin{aligned}
\int \sin^{6}x\cos^{3}x\,dx &= \int \sin^{6}x\cos^{2}x\cdot\cos x\,dx &&\text{save one } \cos x \\
&= \int \sin^{6}x\,(1 - \sin^{2}x)\cos x\,dx &&\cos^{2}x = 1 - \sin^{2}x \\
&= \int u^{6}(1 - u^{2})\,du &&u = \sin x,\ du = \why{\cos x\,dx}{\tfrac{d}{dx}\sin x = \cos x} \\
&= \int (u^{6} - u^{8})\,du &&\text{distribute} \\
&= \why{\frac{u^{7}}{7} - \frac{u^{9}}{9}}{\int u^{n}\,du = \tfrac{u^{n+1}}{n+1} + C} + C &&\text{power rule} \\
&= \boxed{\frac{\sin^{7}x}{7} - \frac{\sin^{9}x}{9} + C} &&u = \sin x
\end{aligned}$$

When sine is the odd one, save $\sin x$ and keep the minus sign in $du$.

$$\begin{aligned} u &= \cos x \\ du &= \why{-\sin x\,dx}{\tfrac{d}{dx}\cos x = -\sin x} \end{aligned}$$

::: checkin
- *Written by Claude* Your turn: $\displaystyle\int \sin^{2}x\cos^{3}x\,dx$  ||  Cosine is odd, so save one $\cos x$.

  $$\begin{aligned}
  \int \sin^{2}x\cos^{3}x\,dx &= \int \sin^{2}x\cos^{2}x\cdot\cos x\,dx &&\text{save one } \cos x \\
  &= \int \sin^{2}x\,(1 - \sin^{2}x)\cos x\,dx &&\cos^{2}x = 1 - \sin^{2}x \\
  &= \int u^{2}(1 - u^{2})\,du &&u = \sin x,\ du = \why{\cos x\,dx}{\tfrac{d}{dx}\sin x = \cos x} \\
  &= \int (u^{2} - u^{4})\,du &&\text{distribute} \\
  &= \tfrac{u^{3}}{3} - \tfrac{u^{5}}{5} + C &&\text{power rule} \\
  &= \boxed{\tfrac{\sin^{3}x}{3} - \tfrac{\sin^{5}x}{5} + C} &&u = \sin x
  \end{aligned}$$
:::

### Case 2: both powers even

When both powers are even, there is nothing to save as $du$. Lower the powers with the power-reducing identities, and write $\sin\theta\cos\theta$ as $\tfrac{1}{2}\sin 2\theta$ when both appear.

$$\int \underbrace{\sin^{2}(2x)}_{\text{even}}\;\underbrace{\cos^{2}(2x)}_{\text{even}}\,dx \qquad \text{nothing to save: reduce the powers}$$

$$\begin{aligned}
\int \sin^{2}(2x)\cos^{2}(2x)\,dx &= \int (\sin 2x\cos 2x)^{2}\,dx &&\text{group as a square} \\
&= \int \left(\tfrac{1}{2}\sin 4x\right)^{2}dx &&\sin 2\theta = 2\sin\theta\cos\theta \text{ with } \theta = 2x \\
&= \frac{1}{4}\int \sin^{2}(4x)\,dx &&\text{square the } \tfrac{1}{2} \\
&= \frac{1}{4}\int \tfrac{1}{2}\left(1 - \cos 8x\right)dx &&\sin^{2}\theta = \tfrac{1}{2}(1 - \cos 2\theta) \text{ with } \theta = 4x \\
&= \frac{1}{8}\int (1 - \cos 8x)\,dx &&\text{multiply the constants} \\
&= \frac{1}{8}\left(x - \frac{\sin 8x}{8}\right) + C &&\int\cos(ax)\,dx = \tfrac{1}{a}\sin(ax) \\
&= \boxed{\frac{x}{8} - \frac{\sin 8x}{64} + C} &&\text{distribute}
\end{aligned}$$

### Case 3: even secant power

When the secant power is even and at least $2$, save one $\sec^{2}x$ as $du$, with $\tan x$ as $u$. Turn the remaining secants into tangents with $\sec^{2}x = 1 + \tan^{2}x$.

$$\int \underbrace{\tan^{5}x}_{\text{any power}}\;\underbrace{\sec^{4}x}_{\text{even: save } \sec^{2}x}\,dx$$

$$\begin{aligned}
\int \tan^{5}x\sec^{4}x\,dx &= \int \tan^{5}x\sec^{2}x\cdot\sec^{2}x\,dx &&\text{save one } \sec^{2}x \\
&= \int \tan^{5}x\,(1 + \tan^{2}x)\sec^{2}x\,dx &&\sec^{2}x = 1 + \tan^{2}x \\
&= \int u^{5}(1 + u^{2})\,du &&u = \tan x,\ du = \why{\sec^{2}x\,dx}{\tfrac{d}{dx}\tan x = \sec^{2}x} \\
&= \int (u^{5} + u^{7})\,du &&\text{distribute} \\
&= \boxed{\frac{\tan^{6}x}{6} + \frac{\tan^{8}x}{8} + C} &&\text{power rule, } u = \tan x
\end{aligned}$$

$\int \frac{\sin^{5}x}{\cos^{9}x}\,dx$ is this same integral, because $\frac{\sin^{5}x}{\cos^{9}x} = \tan^{5}x\sec^{4}x$.

### Case 4: odd tangent power

When the tangent power is odd and there is at least one secant, save $\sec x\tan x$ as $du$, with $\sec x$ as $u$. Turn the remaining tangents into secants with $\tan^{2}x = \sec^{2}x - 1$.

$$\int \underbrace{\tan^{3}x}_{\text{odd: save } \sec x\tan x}\;\underbrace{\sec^{5}x}_{\text{odd: case 3 fails}}\,dx$$

$$\begin{aligned}
\int \tan^{3}x\sec^{5}x\,dx &= \int \tan^{2}x\sec^{4}x\cdot\sec x\tan x\,dx &&\text{save } \sec x\tan x \\
&= \int (\sec^{2}x - 1)\sec^{4}x\cdot\sec x\tan x\,dx &&\tan^{2}x = \sec^{2}x - 1 \\
&= \int (u^{2} - 1)u^{4}\,du &&u = \sec x,\ du = \why{\sec x\tan x\,dx}{\tfrac{d}{dx}\sec x = \sec x\tan x} \\
&= \int (u^{6} - u^{4})\,du &&\text{distribute} \\
&= \boxed{\frac{\sec^{7}x}{7} - \frac{\sec^{5}x}{5} + C} &&\text{power rule, } u = \sec x
\end{aligned}$$

$\int \cot^{3}x\csc^{5}x\,dx$ runs the same way with $u = \csc x$.

$$\begin{aligned}
\int \cot^{3}x\csc^{5}x\,dx &= \int \cot^{2}x\csc^{4}x\cdot\csc x\cot x\,dx &&\text{save } \csc x\cot x \\
&= \int (\csc^{2}x - 1)\csc^{4}x\cdot\csc x\cot x\,dx &&\cot^{2}x = \csc^{2}x - 1 \\
&= -\int (u^{2} - 1)u^{4}\,du &&u = \csc x,\ du = \why{-\csc x\cot x\,dx}{\tfrac{d}{dx}\csc x = -\csc x\cot x} \\
&= -\int (u^{6} - u^{4})\,du &&\text{distribute} \\
&= \boxed{-\tfrac{1}{7}\csc^{7}x + \tfrac{1}{5}\csc^{5}x + C} &&\text{power rule, } u = \csc x
\end{aligned}$$

### The one that needs parts: $\int \csc^{3}x\,dx$

Odd cosecant with no cotangent fits no case, so run the parts loop from Chapter 1.

$$\int \underbrace{\csc x}_{u}\;\underbrace{\csc^{2}x\,dx}_{dv}$$

$$\boxed{\begin{aligned} u &= \csc x & dv &= \csc^{2}x\,dx \\ du &= \why{-\csc x\cot x\,dx}{\tfrac{d}{dx}\csc x = -\csc x\cot x} & v &= \why{-\cot x}{\int\csc^{2}x\,dx = -\cot x + C} \end{aligned}}$$

$$\begin{aligned}
I &= \int \csc^{3}x\,dx \\
&= -\csc x\cot x - \int (-\cot x)(-\csc x\cot x)\,dx &&uv - \int v\,du \\
&= -\csc x\cot x - \int (\csc^{2}x - 1)\csc x\,dx &&\text{the minus signs cancel; } \cot^{2}x = \csc^{2}x - 1 \\
&= -\csc x\cot x - I + \int \csc x\,dx &&\text{split; } \int\csc^{3} \text{ is } I \\
2I &= -\csc x\cot x - \ln\lvert\csc x + \cot x\rvert &&\text{add } I;\ \int\csc x\,dx \text{ from the table} \\
I &= \boxed{-\tfrac{1}{2}\csc x\cot x - \tfrac{1}{2}\ln\lvert\csc x + \cot x\rvert + C}
\end{aligned}$$

### Checkpoint

*Written by Claude*

::: mcq c2a a
$\displaystyle\int \sin^{3}x\cos^{6}x\,dx$ equals which of these?
- $-\dfrac{\cos^{7}x}{7} + \dfrac{\cos^{9}x}{9} + C$
- $\dfrac{\cos^{7}x}{7} - \dfrac{\cos^{9}x}{9} + C$ || The minus from $du = -\sin x\,dx$ was dropped.
- $-\dfrac{\cos^{7}x}{7} - \dfrac{\cos^{9}x}{9} + C$ || $(1 - u^{2})u^{6}$ was expanded with the wrong sign; it is $u^{6} - u^{8}$.
- $-\dfrac{\sin^{2}x\cos^{7}x}{7} + C$ || $\sin^{2}x$ was left as it is; it must become $1 - \cos^{2}x$ before substituting.
why: Sine is odd, so save one $\sin x$. $$\begin{aligned} \int \sin^{3}x\cos^{6}x\,dx &= \int \sin^{2}x\cos^{6}x\cdot\sin x\,dx &&\text{save one } \sin x \\ &= \int (1 - \cos^{2}x)\cos^{6}x\sin x\,dx &&\sin^{2}x = 1 - \cos^{2}x \\ &= -\int (1 - u^{2})u^{6}\,du &&u = \cos x,\ du = \why{-\sin x\,dx}{\tfrac{d}{dx}\cos x = -\sin x} \\ &= -\int (u^{6} - u^{8})\,du &&\text{distribute} \\ &= -\tfrac{u^{7}}{7} + \tfrac{u^{9}}{9} + C &&\text{power rule} \\ &= \boxed{-\tfrac{\cos^{7}x}{7} + \tfrac{\cos^{9}x}{9} + C} &&u = \cos x \end{aligned}$$
:::

*Written by Claude*

::: mcq c2b c
$\displaystyle\int \sec^{6}x\,dx$ equals which of these?
- $\dfrac{\sec^{7}x}{7} + C$ || The power rule was used on $\sec x$, but $dx$ is not $d(\sec x)$.
- $\tan x - \dfrac{2\tan^{3}x}{3} + \dfrac{\tan^{5}x}{5} + C$ || $\sec^{2}x = 1 + \tan^{2}x$ was used with a minus sign.
- $\tan x + \dfrac{2\tan^{3}x}{3} + \dfrac{\tan^{5}x}{5} + C$
- $\dfrac{\tan^{5}x}{5} + C$ || The $1$ in $1 + \tan^{2}x$ was dropped, so only $\int u^{4}\,du$ is left.
why: Even secant power, so save one $\sec^{2}x$. $$\begin{aligned} \int \sec^{6}x\,dx &= \int \sec^{4}x\cdot\sec^{2}x\,dx &&\text{save one } \sec^{2}x \\ &= \int (1 + \tan^{2}x)^{2}\sec^{2}x\,dx &&\sec^{2}x = 1 + \tan^{2}x \\ &= \int (1 + u^{2})^{2}\,du &&u = \tan x,\ du = \why{\sec^{2}x\,dx}{\tfrac{d}{dx}\tan x = \sec^{2}x} \\ &= \int (1 + 2u^{2} + u^{4})\,du &&\text{expand the square} \\ &= u + \tfrac{2u^{3}}{3} + \tfrac{u^{5}}{5} + C &&\text{power rule} \\ &= \boxed{\tan x + \tfrac{2\tan^{3}x}{3} + \tfrac{\tan^{5}x}{5} + C} &&u = \tan x \end{aligned}$$
:::

## Chapter 3 · Trig Substitution

### Match the form under the root

When a root holds $a^{2}-x^{2}$, $a^{2}+x^{2}$ or $x^{2}-a^{2}$, substitute the $x$ written under its form, so that one identity turns the root into a single trig function.

::: big
$$\underset{x \,=\, a\sin\theta}{a^{2}-x^{2}}\qquad\underset{x \,=\, a\tan\theta}{a^{2}+x^{2}}\qquad\underset{x \,=\, a\sec\theta}{x^{2}-a^{2}}$$
:::

| form under the root | $a^{2} - x^{2}$ | $a^{2} + x^{2}$ | $x^{2} - a^{2}$ |
|---|---|---|---|
| substitute | $x = a\sin\theta$ | $x = a\tan\theta$ | $x = a\sec\theta$ |
| $dx$ | $a\cos\theta\,d\theta$ | $a\sec^{2}\theta\,d\theta$ | $a\sec\theta\tan\theta\,d\theta$ |
| identity that removes the root | $1 - \sin^{2} = \cos^{2}$ | $1 + \tan^{2} = \sec^{2}$ | $\sec^{2} - 1 = \tan^{2}$ |
| the root becomes | $a\cos\theta$ | $a\sec\theta$ | $a\tan\theta$ |

Use it when a root has no matching $du$; the same forms work for powers like $(a^{2}+x^{2})^{3/2}$. Integrate in $\theta$, then read every trig function of $\theta$ off a right triangle drawn from the substitution, and turn a bare $\theta$ into the inverse function.

### Sine form: $\int \dfrac{dx}{x^{2}\sqrt{25-x^{2}}}$

The root holds $25-x^{2}$, which is $a^{2}-x^{2}$ with $a = 5$. Substitute $5\sin\theta$ for $x$, simplify the root, and integrate in $\theta$.

$$\int \frac{dx}{x^{2}\underbrace{\sqrt{25-x^{2}}}_{a^{2}-x^{2},\ a = 5}}$$

$$\begin{aligned}
x &= 5\sin\theta, \qquad dx = \why{5\cos\theta\,d\theta}{\tfrac{d}{d\theta}(a\sin\theta) = a\cos\theta} \\
\sqrt{25 - x^{2}} &= \sqrt{25 - 25\sin^{2}\theta} &&\text{substitute} \\
&= \sqrt{25\cos^{2}\theta} &&1 - \sin^{2}\theta = \cos^{2}\theta \\
&= \why{5\cos\theta}{\sqrt{a^{2}\cos^{2}\theta} = a\cos\theta \text{ when } \cos\theta \ge 0} &&\text{the root is gone}
\end{aligned}$$

$$\begin{aligned}
\int \frac{dx}{x^{2}\sqrt{25-x^{2}}} &= \int \frac{5\cos\theta\,d\theta}{25\sin^{2}\theta\cdot 5\cos\theta} &&x^{2} = 25\sin^{2}\theta \\
&= \int \frac{d\theta}{25\sin^{2}\theta} &&\text{cancel } 5\cos\theta \\
&= \frac{1}{25}\int \csc^{2}\theta\,d\theta &&\tfrac{1}{\sin^{2}} = \csc^{2} \\
&= -\frac{1}{25}\cot\theta + C &&\int\csc^{2}\theta\,d\theta = -\cot\theta
\end{aligned}$$

::: fig raw
{"h":230,"items":[
 {"t":"poly","points":[[120,190],[560,190],[560,50]]},
 {"t":"path","d":"M540 190 L540 170 L560 170"},
 {"t":"text","x":150,"y":178,"text":"θ","size":26},
 {"t":"text","x":320,"y":100,"text":"5  (hypotenuse)","anchor":"middle","size":22},
 {"t":"text","x":600,"y":125,"text":"x","size":24,"hi":true},
 {"t":"text","x":340,"y":218,"text":"√(25 − x²)","anchor":"middle","size":22}
],"caption":"Triangle for $x = 5\\sin\\theta$"}

:::

$\sin\theta = x/5$ puts $x$ opposite and $5$ on the hypotenuse, so Pythagoras gives the adjacent side $\sqrt{25-x^{2}}$.

$$\cot\theta = \why{\frac{\sqrt{25-x^{2}}}{x}}{\cot\theta = \tfrac{\text{adjacent}}{\text{opposite}}}$$

$$\begin{aligned}
-\frac{1}{25}\cot\theta + C &= \boxed{-\frac{\sqrt{25-x^{2}}}{25x} + C} &&\cot\theta \text{ from the triangle}
\end{aligned}$$

::: checkin
- *Written by Claude* Your turn: $\displaystyle\int \frac{dx}{x^{2}\sqrt{36-x^{2}}}$  ||  $36 - x^{2}$ is the sine form with $a = 6$.

  $$\begin{aligned}
  x &= 6\sin\theta, \qquad dx = \why{6\cos\theta\,d\theta}{\tfrac{d}{d\theta}(a\sin\theta) = a\cos\theta} \\
  \sqrt{36 - x^{2}} &= \sqrt{36 - 36\sin^{2}\theta} &&\text{substitute} \\
  &= 6\cos\theta &&1 - \sin^{2}\theta = \cos^{2}\theta
  \end{aligned}$$

  $$\begin{aligned}
  \int \frac{dx}{x^{2}\sqrt{36-x^{2}}} &= \int \frac{6\cos\theta\,d\theta}{36\sin^{2}\theta\cdot 6\cos\theta} &&x^{2} = 36\sin^{2}\theta \\
  &= \int \frac{d\theta}{36\sin^{2}\theta} &&\text{cancel } 6\cos\theta \\
  &= \frac{1}{36}\int \csc^{2}\theta\,d\theta &&\tfrac{1}{\sin^{2}} = \csc^{2} \\
  &= -\frac{1}{36}\cot\theta + C &&\int\csc^{2}\theta\,d\theta = -\cot\theta \\
  &= \boxed{-\frac{\sqrt{36-x^{2}}}{36x} + C} &&\cot\theta = \tfrac{\sqrt{36-x^{2}}}{x} \text{ from the triangle}
  \end{aligned}$$
:::

### Tangent form: $\int \dfrac{dx}{(9+x^{2})^{3/2}}$

The power $(9+x^{2})^{3/2}$ is the cube of $\sqrt{9+x^{2}}$, the form $a^{2}+x^{2}$ with $a = 3$. Substitute $3\tan\theta$ for $x$, so $9+x^{2}$ becomes $9\sec^{2}\theta$.

$$\int \frac{dx}{\underbrace{(9+x^{2})^{3/2}}_{\left(\sqrt{a^{2}+x^{2}}\right)^{3},\ a = 3}}$$

$$x = 3\tan\theta \qquad dx = \why{3\sec^{2}\theta\,d\theta}{\tfrac{d}{d\theta}(a\tan\theta) = a\sec^{2}\theta} \qquad 9 + x^{2} = 9 + 9\tan^{2}\theta = 9\sec^{2}\theta$$

$$\begin{aligned}
\int \frac{dx}{(9+x^{2})^{3/2}} &= \int \frac{3\sec^{2}\theta\,d\theta}{(9\sec^{2}\theta)^{3/2}} &&\text{substitute} \\
&= \int \frac{3\sec^{2}\theta\,d\theta}{27\sec^{3}\theta} &&(9\sec^{2}\theta)^{3/2} = 9^{3/2}\sec^{3}\theta = 27\sec^{3}\theta \\
&= \frac{1}{9}\int \frac{d\theta}{\sec\theta} &&\text{cancel } \sec^{2}\theta \text{ and } 3 \\
&= \frac{1}{9}\int \cos\theta\,d\theta &&\tfrac{1}{\sec} = \cos \\
&= \frac{1}{9}\why{\sin\theta}{\int\cos\theta\,d\theta = \sin\theta + C} + C
\end{aligned}$$

::: fig raw
{"h":230,"items":[
 {"t":"poly","points":[[120,190],[560,190],[560,50]]},
 {"t":"path","d":"M540 190 L540 170 L560 170"},
 {"t":"text","x":150,"y":178,"text":"θ","size":26},
 {"t":"text","x":300,"y":95,"text":"√(x² + 9)","anchor":"middle","size":22},
 {"t":"text","x":600,"y":125,"text":"x","size":24,"hi":true},
 {"t":"text","x":340,"y":218,"text":"3","anchor":"middle","size":24}
],"caption":"Triangle for $x = 3\\tan\\theta$"}

:::

$$\begin{aligned}
\frac{1}{9}\sin\theta + C &= \boxed{\frac{x}{9\sqrt{x^{2}+9}} + C} &&\sin\theta = \tfrac{\text{opp}}{\text{hyp}} = \tfrac{x}{\sqrt{x^{2}+9}}
\end{aligned}$$

### Secant form with a coefficient: $\int \dfrac{3\,dx}{\sqrt{9x^{2}-16}}$

When $x^{2}$ carries a coefficient, write that term as a square: $9x^{2}$ is $(3x)^{2}$, so $3x$ plays the role of $x$ and $a = 4$. Substitute $4\sec\theta$ for $3x$, then solve for $x$ and $dx$.

$$\int \frac{3\,dx}{\sqrt{\underbrace{9x^{2}-16}_{(3x)^{2}-4^{2}}}} \qquad 3x \text{ plays } x,\ a = 4$$

$$3x = 4\sec\theta \qquad x = \tfrac{4}{3}\sec\theta \qquad dx = \why{\tfrac{4}{3}\sec\theta\tan\theta\,d\theta}{\tfrac{d}{d\theta}(c\sec\theta) = c\sec\theta\tan\theta} \qquad \sqrt{9x^{2}-16} = \sqrt{16\sec^{2}\theta - 16} = \why{4\tan\theta}{\sec^{2}\theta - 1 = \tan^{2}\theta}$$

$$\begin{aligned}
\int \frac{3\,dx}{\sqrt{9x^{2}-16}} &= \int \frac{3\cdot\tfrac{4}{3}\sec\theta\tan\theta\,d\theta}{4\tan\theta} &&\text{substitute} \\
&= \int \sec\theta\,d\theta &&\text{cancel } 4 \text{ and } \tan\theta \\
&= \ln\lvert\sec\theta + \tan\theta\rvert + C &&\text{the } \int\sec \text{ row}
\end{aligned}$$

::: fig raw
{"h":230,"items":[
 {"t":"poly","points":[[120,190],[560,190],[560,50]]},
 {"t":"path","d":"M540 190 L540 170 L560 170"},
 {"t":"text","x":150,"y":178,"text":"θ","size":26},
 {"t":"text","x":300,"y":95,"text":"3x","anchor":"middle","size":24,"hi":true},
 {"t":"text","x":585,"y":125,"text":"√(9x² − 16)","size":22},
 {"t":"text","x":340,"y":218,"text":"4","anchor":"middle","size":24}
],"caption":"Triangle for $3x = 4\\sec\\theta$"}

:::

$$\begin{aligned}
\ln\lvert\sec\theta + \tan\theta\rvert + C &= \boxed{\ln\left\lvert\frac{3x}{4} + \frac{\sqrt{9x^{2}-16}}{4}\right\rvert + C} &&\sec\theta = \tfrac{3x}{4},\ \tan\theta = \tfrac{\sqrt{9x^{2}-16}}{4}
\end{aligned}$$

Clearing the $4$'s gives $\ln\lvert 3x + \sqrt{9x^{2}-16}\rvert + C$, which differs by the constant $\ln 4$ and is equally correct.

### The root alone: $\int \sqrt{16-x^{2}}\,dx$

When the integrand is the root alone, $\sqrt{16-x^{2}}$ is the sine form with $a = 4$. The substitution leaves $\cos^{2}\theta$, so reduce the power before you integrate, and convert back with the triangle.

$$\int \underbrace{\sqrt{16-x^{2}}}_{a = 4}\,dx \qquad \text{leaves } \cos^{2}\theta \text{: Chapter 2 case 2}$$

$$x = 4\sin\theta \qquad dx = \why{4\cos\theta\,d\theta}{\tfrac{d}{d\theta}(a\sin\theta) = a\cos\theta} \qquad \sqrt{16-x^{2}} = 4\cos\theta$$

$$\begin{aligned}
\int \sqrt{16-x^{2}}\,dx &= \int 4\cos\theta\cdot 4\cos\theta\,d\theta &&\text{substitute} \\
&= 16\int \cos^{2}\theta\,d\theta \\
&= 16\int \tfrac{1}{2}(1 + \cos 2\theta)\,d\theta &&\text{power reducing} \\
&= 8\left(\theta + \frac{\sin 2\theta}{2}\right) + C &&\int\cos 2\theta\,d\theta = \tfrac{1}{2}\sin 2\theta \\
&= 8\theta + 4\cdot 2\sin\theta\cos\theta + C &&\sin 2\theta = 2\sin\theta\cos\theta \\
&= 8\sin^{-1}\!\left(\frac{x}{4}\right) + 8\cdot\frac{x}{4}\cdot\frac{\sqrt{16-x^{2}}}{4} + C &&\theta = \sin^{-1}\tfrac{x}{4},\ \cos\theta = \tfrac{\sqrt{16-x^{2}}}{4} \\
&= \boxed{8\sin^{-1}\!\left(\frac{x}{4}\right) + \frac{x\sqrt{16-x^{2}}}{2} + C} &&8\cdot\tfrac{1}{16} = \tfrac{1}{2}
\end{aligned}$$

Rewrite $\sin 2\theta$ as $2\sin\theta\cos\theta$ before reading the triangle.

### A middle term: complete the square first

When the expression under the root has an $x$ term, complete the square first. That rewrites it as $(x+h)^{2}$ plus a constant, and with $x+h$ as $u$ it is one of the three forms.

$$\sqrt{\underbrace{x^{2}-6x+5}_{\text{matches no form yet}}}$$

$$\begin{aligned}
x^{2} - 6x + 5 &= (x^{2} - 6x + 9) - 9 + 5 &&\text{add and subtract } (6/2)^{2} = 9 \\
&= (x-3)^{2} - 4 &&\text{perfect square}
\end{aligned}$$

Substitute, and the root becomes the secant form with $a = 2$.

$$\begin{aligned} u &= x - 3 \\ du &= dx \\ \sqrt{x^{2}-6x+5} &= \sqrt{u^{2}-4} &&\text{the completed square} \end{aligned}$$

### Checkpoint

*Written by Claude*

::: mcq c3a d
Which substitution turns $\displaystyle\int \frac{dx}{x^{2}\sqrt{x^{2}+1}}$ into a trig integral with no root left?
- $x = \sin\theta$, because $\sqrt{1-\sin^{2}\theta}$ becomes $\cos\theta$ || Sine is for $1 - x^{2}$; here the root holds $x^{2} + 1$.
- $x = \sec\theta$, because $\sqrt{\sec^{2}\theta-1}$ becomes $\tan\theta$ || Secant is for $x^{2} - 1$; here it would give $\sqrt{\sec^{2}\theta + 1}$, not a square.
- $u = x^{2}+1$, because $\sqrt{x^{2}+1}$ becomes $\sqrt{u}$ || There is no $x\,dx$ upstairs, so the $du = 2x\,dx$ this needs is missing.
- $x = \tan\theta$, because $\sqrt{\tan^{2}\theta+1}$ becomes $\sec\theta$
why: The root holds $x^{2} + 1$, the form $a^{2} + x^{2}$ with $a = 1$, so tangent. $$\begin{aligned} x &= \tan\theta \\ \sqrt{x^{2}+1} &= \sqrt{\tan^{2}\theta + 1} &&\text{substitute} \\ &= \sqrt{\sec^{2}\theta} &&1 + \tan^{2}\theta = \sec^{2}\theta \\ &= \boxed{\sec\theta} &&\text{no root left} \end{aligned}$$
:::

*Written by Claude*

::: mcq c3b b
$\displaystyle\int \frac{dx}{x^{2}\sqrt{49-x^{2}}}$ equals which of these?
- $-\dfrac{\sqrt{49-x^{2}}}{7x} + C$ || $x^{2}$ was written as $7\sin^{2}\theta$; $(7\sin\theta)^{2} = 49\sin^{2}\theta$.
- $-\dfrac{\sqrt{49-x^{2}}}{49x} + C$
- $\dfrac{\sqrt{49-x^{2}}}{49x} + C$ || The minus in $\int\csc^{2}\theta\,d\theta = -\cot\theta$ was dropped.
- $-\dfrac{x}{49\sqrt{49-x^{2}}} + C$ || This reads $\tan\theta$ off the triangle instead of $\cot\theta$.
why: $49 - x^{2}$ is the sine form, so $x = 7\sin\theta$. $$\begin{aligned} \int \frac{dx}{x^{2}\sqrt{49-x^{2}}} &= \int \frac{7\cos\theta\,d\theta}{49\sin^{2}\theta\cdot 7\cos\theta} &&dx = \why{7\cos\theta\,d\theta}{\tfrac{d}{d\theta}(a\sin\theta) = a\cos\theta},\ \sqrt{49-x^{2}} = 7\cos\theta \\ &= \frac{1}{49}\int\csc^{2}\theta\,d\theta &&\text{cancel } 7\cos\theta \\ &= -\frac{1}{49}\cot\theta + C &&\int\csc^{2}\theta\,d\theta = -\cot\theta \\ &= \boxed{-\frac{\sqrt{49-x^{2}}}{49x} + C} &&\cot\theta = \tfrac{\sqrt{49-x^{2}}}{x} \text{ from the triangle} \end{aligned}$$
:::

## Chapter 4 · Partial Fractions

### The decomposition shapes

Use partial fractions on a ratio of polynomials: split it into the simple fractions below, built from the factors of the bottom, and integrate each one.

::: big
$$\underset{(x-r)}{\frac{A}{x-r}}\qquad\underset{(x-r)^{2}:\ \text{one term per power}}{\frac{A}{x-r}+\frac{B}{(x-r)^{2}}}\qquad\underset{\text{irreducible } x^{2}+bx+c:\ \text{linear top}}{\frac{Ax+B}{x^{2}+bx+c}}$$
:::

First make the top's degree smaller than the bottom's (divide if not), then factor the bottom completely. Multiply through by the bottom, then find the constants by plugging in roots or matching coefficients.

### Two linear factors, definite: $\int_{2}^{8} \dfrac{x+5}{x^{2}+10x}\,dx$

When the bottom factors into distinct linear factors, give each factor its own constant over it. Multiply through by the bottom and plug in each root to find the constants.

$$\frac{\overbrace{x+5}^{\deg 1}}{\underbrace{x(x+10)}_{x^{2}+10x,\ \deg 2}} = \frac{A}{x} + \frac{B}{x+10}$$

$$\begin{aligned}
x + 5 &= A(x+10) + Bx &&\text{multiply by } x(x+10) \\
5 &= 10A &&\text{plug in } x = 0 \text{ to kill the } B \text{ term} \\
A &= \tfrac{1}{2} \\
-5 &= -10B &&\text{plug in } x = -10 \text{ to kill the } A \text{ term} \\
B &= \tfrac{1}{2}
\end{aligned}$$

$$\begin{aligned}
\int_{2}^{8} \frac{x+5}{x^{2}+10x}\,dx &= \int_{2}^{8}\left(\frac{1/2}{x} + \frac{1/2}{x+10}\right)dx &&\text{the decomposition} \\
&= \frac{1}{2}\Big[\ln\lvert x\rvert + \why{\ln\lvert x+10\rvert}{\int\tfrac{dx}{x+c} = \ln\lvert x+c\rvert + C}\Big]_{2}^{8} &&\int\tfrac{1}{x} \text{ rows} \\
&= \frac{1}{2}\Big[(\ln 8 + \ln 18) - (\ln 2 + \ln 12)\Big] &&\text{upper minus lower} \\
&= \frac{1}{2}\ln\frac{8\cdot 18}{2\cdot 12} &&\ln a + \ln b = \ln ab,\ \ln a - \ln b = \ln\tfrac{a}{b} \\
&= \boxed{\tfrac{1}{2}\ln 6} &&\tfrac{144}{24} = 6
\end{aligned}$$

::: checkin
- *Written by Claude* Your turn: $\displaystyle\int_{2}^{10} \frac{x+3}{x^{2}+6x}\,dx$  ||  The bottom is $x(x+6)$, two linear factors.

  $$\frac{x+3}{x(x+6)} = \frac{A}{x} + \frac{B}{x+6}$$

  $$\begin{aligned}
  x + 3 &= A(x+6) + Bx &&\text{multiply by } x(x+6) \\
  3 &= 6A &&\text{plug in } x = 0 \text{ to kill the } B \text{ term} \\
  A &= \tfrac{1}{2} \\
  -3 &= -6B &&\text{plug in } x = -6 \text{ to kill the } A \text{ term} \\
  B &= \tfrac{1}{2}
  \end{aligned}$$

  $$\begin{aligned}
  \int_{2}^{10} \frac{x+3}{x^{2}+6x}\,dx &= \frac{1}{2}\Big[\ln\lvert x\rvert + \ln\lvert x+6\rvert\Big]_{2}^{10} &&\int\tfrac{1}{x} \text{ rows} \\
  &= \frac{1}{2}\Big[(\ln 10 + \ln 16) - (\ln 2 + \ln 8)\Big] &&\text{upper minus lower} \\
  &= \boxed{\tfrac{1}{2}\ln 10} &&\ln 2 + \ln 8 = \ln 16 \text{ cancels}
  \end{aligned}$$
:::

### Degree too big: $\int \dfrac{x^{2}+3}{x^{2}-4x+3}\,dx$

When the degree of the top is at least the degree of the bottom, divide first. Integrate the quotient directly and decompose only the remainder over the bottom.

$$\frac{\overbrace{x^{2}+3}^{\deg 2}}{\underbrace{x^{2}-4x+3}_{\deg 2}} \qquad \deg \text{top} \ge \deg \text{bottom}: \text{ divide first}$$

$$\begin{aligned}
x^{2} + 3 &= 1\cdot(x^{2} - 4x + 3) + \text{remainder} &&\text{quotient } 1 \\
\text{remainder} &= (x^{2} + 3) - (x^{2} - 4x + 3) \\
&= 4x &&\text{degree 1, smaller than 2: stop} \\
\frac{x^{2}+3}{x^{2}-4x+3} &= 1 + \frac{4x}{(x-1)(x-3)} &&\text{quotient} + \tfrac{\text{remainder}}{\text{bottom}},\ \text{bottom factored}
\end{aligned}$$

$$\begin{aligned}
4x &= A(x-3) + B(x-1) &&\text{multiply by } (x-1)(x-3) \\
4 &= -2A &&\text{plug in } x = 1 \\
A &= -2 \\
12 &= 2B &&\text{plug in } x = 3 \\
B &= 6
\end{aligned}$$

$$\begin{aligned}
\int \frac{x^{2}+3}{x^{2}-4x+3}\,dx &= \int \left(1 - \frac{2}{x-1} + \frac{6}{x-3}\right)dx \\
&= \boxed{x - 2\ln\lvert x-1\rvert + \why{6\ln\lvert x-3\rvert}{\int\tfrac{k\,dx}{x-r} = k\ln\lvert x-r\rvert + C} + C}
\end{aligned}$$

### Repeated linear factor: $\int \dfrac{x+5}{(x+1)(x^{2}-6x+9)}\,dx$

When a linear factor is squared, it gets two terms: one over the factor and one over its square. Factor $x^{2}-6x+9$ as $(x-3)^{2}$ first so you can see it.

$$\frac{x+5}{(x+1)\underbrace{(x-3)^{2}}_{x^{2}-6x+9}} = \frac{A}{x+1} + \underbrace{\frac{B}{x-3} + \frac{D}{(x-3)^{2}}}_{\text{two terms for the square}}$$

Call the third constant $D$ so it does not collide with the $+C$ at the end.

$$\begin{aligned}
x + 5 &= A(x-3)^{2} + B(x+1)(x-3) + D(x+1) &&\text{multiply by } (x+1)(x-3)^{2} \\
4 &= A(-4)^{2} &&\text{plug in } x = -1 \\
A &= \tfrac{1}{4} \\
8 &= D(4) &&\text{plug in } x = 3 \\
D &= 2 \\
5 &= \tfrac{1}{4}(9) + B(1)(-3) + 2(1) &&\text{plug in } x = 0,\ \text{with } A, D \text{ known} \\
5 &= \tfrac{17}{4} - 3B \\
B &= -\tfrac{1}{4}
\end{aligned}$$

$$\begin{aligned}
\int \frac{x+5}{(x+1)(x-3)^{2}}\,dx &= \int \left(\frac{1/4}{x+1} - \frac{1/4}{x-3} + \frac{2}{(x-3)^{2}}\right)dx \\
&= \tfrac{1}{4}\ln\lvert x+1\rvert - \tfrac{1}{4}\ln\lvert x-3\rvert - \frac{2}{x-3} + C &&\int (x-3)^{-2}dx = -(x-3)^{-1} \\
&= \boxed{\tfrac{1}{4}\ln\left\lvert\frac{x+1}{x-3}\right\rvert - \frac{2}{x-3} + C} &&\ln a - \ln b = \ln\tfrac{a}{b}
\end{aligned}$$

### Irreducible quadratic: $\int \dfrac{4x+7}{x^{3}+x}\,dx$

When the bottom has a quadratic factor with no real roots, its term gets a linear top $Bx + D$. Plug in the real root first, then match coefficients for the rest.

$$\frac{4x+7}{x\underbrace{(x^{2}+1)}_{\text{no real roots}}} = \frac{A}{x} + \frac{\overbrace{Bx + D}^{\text{linear top}}}{x^{2}+1}$$

$$\begin{aligned}
4x + 7 &= A(x^{2}+1) + (Bx + D)\,x &&\text{multiply by } x(x^{2}+1) \\
7 &= A &&\text{plug in } x = 0 \\
4x + 7 &= 7x^{2} + 7 + Bx^{2} + Dx &&\text{expand with } A = 7 \\
0 &= 7 + B &&\text{match } x^{2} \text{ coefficients} \\
B &= -7 \\
4 &= D &&\text{match } x \text{ coefficients}
\end{aligned}$$

$$\begin{aligned}
\int \frac{4x+7}{x^{3}+x}\,dx &= \int \frac{7}{x}\,dx + \int \underbrace{\frac{-7x}{x^{2}+1}}_{u = x^{2}+1}\,dx + \int \underbrace{\frac{4}{x^{2}+1}}_{\tan^{-1}}\,dx \\
&= 7\ln\lvert x\rvert - \tfrac{7}{2}\ln(x^{2}+1) + \why{4\tan^{-1}x}{\int\tfrac{dx}{x^{2}+1} = \tan^{-1}x + C} + C &&\int\tfrac{2x}{x^{2}+1}dx = \ln(x^{2}+1);\ -7 = -\tfrac{7}{2}\cdot 2
\end{aligned}$$

$$\boxed{7\ln\lvert x\rvert - \tfrac{7}{2}\ln(x^{2}+1) + 4\tan^{-1}x + C}$$

No bars are needed on $\ln(x^{2}+1)$, since $x^{2}+1$ is always positive.

### When the quadratic piece has a middle term

When a decomposition leaves a constant over an irreducible quadratic with an $x$ term, the antiderivative is an arctangent.

$$\int \frac{dx}{\underbrace{x^{2}-4x+13}_{16 - 52 < 0:\ \text{irreducible}}}$$

Complete the square, then use the arctangent row $\int \frac{du}{u^{2}+a^{2}} = \frac{1}{a}\tan^{-1}\frac{u}{a}$.

$$\begin{aligned}
\int \frac{dx}{x^{2}-4x+13} &= \int \frac{dx}{(x-2)^{2} + 9} &&x^{2}-4x+4 = (x-2)^{2},\ 13 - 4 = 9 \\
&= \int \frac{du}{u^{2} + 3^{2}} &&u = x-2,\ du = dx \\
&= \frac{1}{3}\tan^{-1}\frac{u}{3} + C &&\text{arctangent row, } a = 3 \\
&= \boxed{\frac{1}{3}\tan^{-1}\!\left(\frac{x-2}{3}\right) + C}
\end{aligned}$$

### Checkpoint

*Written by Claude*

::: mcq c4a c
Which is the correct partial-fraction form for $\dfrac{3x-2}{x^{2}(x+4)}$?
- $\dfrac{A}{x^{2}} + \dfrac{B}{x+4}$ || The squared factor needs a term for each power, $\tfrac{A}{x}$ and $\tfrac{B}{x^{2}}$.
- $\dfrac{A}{x} + \dfrac{B}{x+4}$ || $x^{2}$ is a repeated factor, so it needs a $\tfrac{B}{x^{2}}$ term too.
- $\dfrac{A}{x} + \dfrac{B}{x^{2}} + \dfrac{D}{x+4}$
- $\dfrac{A}{x} + \dfrac{B}{x+4} + \dfrac{D}{(x+4)^{2}}$ || The repeated terms went to $x+4$, which appears once; $x$ is the squared factor.
why: $x^{2}$ is the linear factor $x$ raised to the power 2, so it contributes two terms, over $x$ and over $x^{2}$. $$\begin{aligned} 3x - 2 &= Ax(x+4) + B(x+4) + Dx^{2} &&\text{multiply by } x^{2}(x+4) \\ -2 &= 4B &&\text{plug in } x = 0 \\ B &= -\tfrac{1}{2} \\ -14 &= 16D &&\text{plug in } x = -4 \\ D &= -\tfrac{7}{8} \\ 0 &= A + D &&\text{match } x^{2} \text{ coefficients} \\ A &= \tfrac{7}{8} \\ \frac{3x-2}{x^{2}(x+4)} &= \boxed{\frac{7/8}{x} - \frac{1/2}{x^{2}} - \frac{7/8}{x+4}} &&\text{the decomposition} \end{aligned}$$
:::

*Written by Claude*

::: mcq c4b a
$\displaystyle\int_{1}^{3} \frac{x+4}{x^{2}+2x}\,dx$ equals which of these?
- $3\ln 3 - \ln 5$
- $\ln 3 + \ln 5$ || $B$ came out as $+1$; plugging in $x = -2$ gives it the opposite sign.
- $2\ln 3 - \ln 5$ || The lower limit was dropped from the second term: $-\ln(1+2) = -\ln 3$.
- $2\ln 5 - 3\ln 3$ || $A$ and $B$ were swapped; $x = 0$ gives the constant over $x$.
why: The bottom is $x(x+2)$, two linear factors. $$\begin{aligned} x + 4 &= A(x+2) + Bx &&\text{multiply by } x(x+2) \\ 4 &= 2A &&\text{plug in } x = 0 \\ A &= 2 \\ 2 &= -2B &&\text{plug in } x = -2 \\ B &= -1 \end{aligned}$$ $$\begin{aligned} \int_{1}^{3} \frac{x+4}{x^{2}+2x}\,dx &= \int_{1}^{3}\left(\frac{2}{x} - \frac{1}{x+2}\right)dx &&\text{the decomposition} \\ &= \Big[2\ln x - \ln(x+2)\Big]_{1}^{3} &&\int\tfrac{1}{x} \text{ rows} \\ &= (2\ln 3 - \ln 5) - (2\ln 1 - \ln 3) &&\text{upper minus lower} \\ &= (2\ln 3 - \ln 5) - (0 - \ln 3) &&\ln 1 = 0 \\ &= \boxed{3\ln 3 - \ln 5} &&\text{collect } \ln 3 \end{aligned}$$
:::

## Chapter 5 · L'Hôpital's Rule

### Check the form first

To decide whether L'Hôpital applies, plug the point in and read the form off the result.

::: big
$$\underset{\text{L'Hôpital}}{\boxed{\tfrac{0}{0}\ \ \tfrac{\infty}{\infty}}}\quad\underset{\text{make a fraction}}{0\cdot\infty\ \ \infty-\infty}\quad\underset{\text{take } \ln}{1^{\infty}\ \ 0^{0}\ \ \infty^{0}}$$
:::

Plug in first: any form outside these seven, like $\frac{0}{5}$, $\frac{5}{0^{+}}$ or $0^{\infty}$, is decided by the plug-in. On $\frac{0}{0}$ or $\frac{\infty}{\infty}$, differentiate the top and the bottom separately, not with the quotient rule, and check the form again before each repeat.

$$\lim_{x\to\infty} e^{x} = \infty \qquad \lim_{x\to\infty}\frac{1}{x} = 0 \qquad \lim_{x\to\infty}\ln x = \infty \qquad \lim_{x\to 0^{+}}\ln x = -\infty$$

### $\frac{0}{0}$ twice, and $\frac{\infty}{\infty}$

When plugging in gives $\frac{0}{0}$ or $\frac{\infty}{\infty}$, differentiate the top and the bottom separately and take the limit again. If the new limit is still $\frac{0}{0}$ or $\frac{\infty}{\infty}$, apply the rule again.

$$\begin{aligned}
\lim_{x\to 0}\frac{e^{2x} - 1 - 2x}{x^{2}} &\qquad e^{0} - 1 - 0 = 0,\ 0^{2} = 0:\ \tfrac{0}{0} \\
&= \lim_{x\to 0}\frac{\why{2e^{2x}}{\tfrac{d}{dx}e^{ax} = ae^{ax}} - 2}{2x} &&\text{L'Hôpital; chain rule on } e^{2x} \\
&= \lim_{x\to 0}\frac{e^{2x} - 1}{x} &&\text{cancel } 2;\ e^{0} - 1 = 0 \text{ over } 0:\ \tfrac{0}{0} \text{ again} \\
&= \lim_{x\to 0}\frac{\why{2e^{2x}}{\tfrac{d}{dx}e^{ax} = ae^{ax}}}{1} &&\text{L'Hôpital again} \\
&= \frac{2}{1} &&e^{0} = 1 \\
&= \boxed{2}
\end{aligned}$$

::: checkin
- *Written by Claude* Your turn: $\displaystyle\lim_{x\to 0}\frac{e^{3x} - 1 - 3x}{x^{2}}$  ||  Plug in: $e^{0} - 1 - 0 = 0$ over $0$, so the form is $\tfrac{0}{0}$.

  $$\begin{aligned}
  \lim_{x\to 0}\frac{e^{3x} - 1 - 3x}{x^{2}} &= \lim_{x\to 0}\frac{\why{3e^{3x}}{\tfrac{d}{dx}e^{ax} = ae^{ax}} - 3}{2x} &&\text{L'Hôpital; chain rule on top} \\
  &= \lim_{x\to 0}\frac{\why{9e^{3x}}{\tfrac{d}{dx}e^{ax} = ae^{ax}}}{2} &&3e^{0} - 3 = 0 \text{ over } 0:\ \tfrac{0}{0};\ \text{L'Hôpital again} \\
  &= \boxed{\tfrac{9}{2}} &&e^{0} = 1
  \end{aligned}$$
:::

Powers of $x$ beat $\ln x$, and $e^{x}$ beats powers of $x$.

$$\begin{aligned}
\lim_{x\to\infty}\frac{\ln x}{x} &= \lim_{x\to\infty}\frac{1/x}{1} &&\tfrac{\infty}{\infty};\ \text{L'Hôpital} \\
&= \boxed{0} &&\lim_{x\to\infty}\tfrac{1}{x} = 0
\end{aligned}$$

$$\begin{aligned}
\lim_{x\to\infty}\frac{x^{2}}{e^{x}} &= \lim_{x\to\infty}\frac{2x}{e^{x}} &&\tfrac{\infty}{\infty};\ \text{L'Hôpital} \\
&= \lim_{x\to\infty}\frac{2}{e^{x}} &&\tfrac{\infty}{\infty} \text{ again} \\
&= \boxed{0} &&\lim_{x\to\infty} e^{x} = \infty
\end{aligned}$$

### The rule: L'Hôpital's rule, for $\frac{0}{0}$ and $\frac{\infty}{\infty}$ only

L'Hôpital's rule replaces the limit of a quotient by the limit of the derivative of the top over the derivative of the bottom.

::: key
$$\lim_{x\to a}\frac{f(x)}{g(x)} = \lim_{x\to a}\frac{f'(x)}{g'(x)}$$
:::

It holds when the left side has the form $\frac{0}{0}$ or $\frac{\infty}{\infty}$ and the right side exists.

### $0\cdot\infty$: move one factor downstairs

When the limit is a product with one factor going to $0$ and the other to $\infty$, move one factor to the bottom as $1$ over its reciprocal. That gives $\frac{0}{0}$ or $\frac{\infty}{\infty}$, so L'Hôpital applies.

$$\lim_{x\to 0^{+}} \underbrace{x^{2}}_{\to 0}\,\underbrace{(\ln x)^{2}}_{\to\infty} \qquad \text{keep the log on top, send } x^{2} \text{ down as } \tfrac{1}{1/x^{2}}$$

$$\begin{aligned}
\lim_{x\to 0^{+}} x^{2}(\ln x)^{2} &= \lim_{x\to 0^{+}}\frac{(\ln x)^{2}}{1/x^{2}} &&0\cdot\infty \to \tfrac{\infty}{\infty} \\
&= \lim_{x\to 0^{+}}\frac{2\ln x\cdot\frac{1}{x}}{\why{-2/x^{3}}{\tfrac{d}{dx}x^{-2} = -2x^{-3}}} &&\text{L'Hôpital; chain rule on } (\ln x)^{2} \\
&= \lim_{x\to 0^{+}}\left(-x^{2}\ln x\right) &&\tfrac{2}{x}\div\tfrac{-2}{x^{3}} = -x^{2} \\
&= \lim_{x\to 0^{+}}\frac{-\ln x}{1/x^{2}} &&0\cdot\infty \text{ again; downstairs again} \\
&= \lim_{x\to 0^{+}}\frac{-1/x}{-2/x^{3}} &&\text{L'Hôpital} \\
&= \lim_{x\to 0^{+}} \frac{x^{2}}{2} &&\text{simplify} \\
&= \boxed{0}
\end{aligned}$$

### $\infty - \infty$: combine into one fraction

When the limit is a difference of two terms that both go to $\infty$, combine them into one fraction over a common denominator. Check the new form, then use L'Hôpital.

$$\lim_{x\to 0^{+}}\Big(\underbrace{\tfrac{1}{x}}_{\to\infty} - \underbrace{\tfrac{1}{e^{x}-1}}_{\to\infty}\Big) \qquad \text{common denominator gives } \tfrac{0}{0}$$

$$\begin{aligned}
\lim_{x\to 0^{+}}\left(\frac{1}{x} - \frac{1}{e^{x}-1}\right) &= \lim_{x\to 0^{+}}\frac{e^{x} - 1 - x}{x(e^{x}-1)} &&\text{common denominator } x(e^{x}-1);\ \tfrac{0}{0} \\
&= \lim_{x\to 0^{+}}\frac{e^{x} - 1}{(e^{x} - 1) + xe^{x}} &&\text{L'Hôpital; product rule on } x(e^{x}-1) \\
&= \lim_{x\to 0^{+}}\frac{e^{x}}{e^{x} + e^{x} + xe^{x}} &&\tfrac{0}{0} \text{ again; L'Hôpital, product rule on } xe^{x} \\
&= \boxed{\tfrac{1}{2}} &&\text{plug in } 0
\end{aligned}$$

### $1^{\infty}$, $\infty^{0}$, $0^{0}$: take the logarithm

When a power with a variable base and a variable exponent has the form $1^{\infty}$, $\infty^{0}$ or $0^{0}$, take the natural log of it. The log brings the exponent down as a factor; find the limit $L$ of the log, and the answer is $e^{L}$.

$$\begin{aligned}
y &= f^{\,g} &&\text{name the power} \\
\ln y &= g\ln f &&\text{now a } 0\cdot\infty \\
\lim \ln y &= L &&\text{downstairs, then L'Hôpital} \\
\lim y &= \boxed{e^{L}} &&\text{the answer}
\end{aligned}$$

$$\lim_{x\to\infty}\Big(\underbrace{1 - \tfrac{3}{x}}_{\to 1}\Big)^{\overbrace{2x}^{\to\infty}}$$

$$\begin{aligned}
y &= \left(1 - \tfrac{3}{x}\right)^{2x} \\
\ln y &= 2x\ln\left(1 - \tfrac{3}{x}\right) &&\ln a^{b} = b\ln a;\ \infty\cdot 0 \\
\lim_{x\to\infty}\ln y &= \lim_{x\to\infty}\frac{2\ln\left(1 - \tfrac{3}{x}\right)}{1/x} &&\text{downstairs: } \tfrac{0}{0} \\
&= \lim_{x\to\infty}\frac{2\cdot\frac{1}{1-3/x}\cdot\frac{3}{x^{2}}}{-1/x^{2}} &&\text{L'Hôpital; chain rule on } \ln(1 - 3/x) \\
&= \lim_{x\to\infty}\frac{-6}{1 - 3/x} &&\text{cancel } \tfrac{1}{x^{2}} \\
&= -6 &&\lim_{x\to\infty}\tfrac{3}{x} = 0 \\
\lim_{x\to\infty} y &= \boxed{e^{-6}} &&y = e^{\ln y}
\end{aligned}$$

In general $\lim_{x\to\infty}\left(1 + \frac{a}{x}\right)^{bx} = e^{ab}$, but write the log steps anyway.

$$\lim_{x\to\infty}\big(\underbrace{x + e^{3x}}_{\to\infty}\big)^{\overbrace{1/x}^{\to 0}}$$

$$\begin{aligned}
\ln y &= \frac{\ln(x + e^{3x})}{x} &&\tfrac{\infty}{\infty} \\
\lim_{x\to\infty}\ln y &= \lim_{x\to\infty}\frac{1 + 3e^{3x}}{x + e^{3x}} &&\text{L'Hôpital; chain rule, then divide by } 1;\ \tfrac{\infty}{\infty} \\
&= \lim_{x\to\infty}\frac{9e^{3x}}{1 + 3e^{3x}} &&\text{L'Hôpital again; } \tfrac{\infty}{\infty} \\
&= \lim_{x\to\infty}\frac{27e^{3x}}{9e^{3x}} &&\text{L'Hôpital again} \\
&= 3 \\
\lim_{x\to\infty} y &= \boxed{e^{3}}
\end{aligned}$$

$$\lim_{x\to 0^{+}} x^{x} \qquad 0^{0}$$

$$\begin{aligned}
\ln y &= x\ln x &&0\cdot\infty \\
&= \frac{\ln x}{1/x} &&\text{downstairs: } \tfrac{\infty}{\infty} \\
\lim_{x\to 0^{+}}\ln y &= \lim_{x\to 0^{+}}\frac{1/x}{-1/x^{2}} &&\text{L'Hôpital} \\
&= \lim_{x\to 0^{+}}(-x) = 0 \\
\lim_{x\to 0^{+}} x^{x} &= e^{0} = \boxed{1}
\end{aligned}$$

### Plugging in can already give the answer

When plugging in gives a form that is not indeterminate, like $\frac{0}{-2}$, that value is the limit.

$$\lim_{x\to 0}\frac{\overbrace{x\sin x}^{0\cdot 0 \,=\, 0}}{\underbrace{e^{x} - 3}_{1 - 3 \,=\, -2}}$$

$$\lim_{x\to 0}\frac{x\sin x}{e^{x} - 3} = \frac{0}{-2} = \boxed{0}$$

Write "$\frac{0}{-2}$, not indeterminate" and stop; no derivative is taken.

### Checkpoint

*Written by Claude*

::: mcq c5a d
$\displaystyle\lim_{x\to 0}\frac{x\cos x}{e^{x} - 2}$ equals which of these?
- $-1$ || The factor $x$ upstairs was dropped.
- $1$ || L'Hôpital was used on $\tfrac{0}{-1}$, which is not indeterminate.
- $-\tfrac{1}{2}$ || The factor $x$ was dropped and $e^{0}$ was taken as $0$; $e^{0} = 1$.
- $0$
why: Plug in first: the form is $\frac{0}{-1}$, not indeterminate. $$\begin{aligned} \lim_{x\to 0}\frac{x\cos x}{e^{x} - 2} &= \frac{0\cdot 1}{1 - 2} &&\text{plug in} \\ &= \frac{0}{-1} &&\text{not indeterminate} \\ &= \boxed{0} \end{aligned}$$
:::

*Written by Claude*

::: mcq c5b b
$\displaystyle\lim_{x\to\infty}\left(1 + \frac{4}{x}\right)^{x/2}$ equals which of these?
- $1$ || $1^{\infty}$ was read as $1$; the base is above $1$ while the exponent grows.
- $e^{2}$
- $e^{9/2}$ || The constants were added; the limit is $e^{ab}$ with $ab = 4\cdot\tfrac{1}{2}$.
- $e^{8}$ || The constants were divided; the limit is $e^{ab}$ with $ab = 2$.
why: $1^{\infty}$ form, so take the logarithm. $$\begin{aligned} \ln y &= \tfrac{x}{2}\ln\left(1 + \tfrac{4}{x}\right) &&\ln a^{b} = b\ln a;\ \infty\cdot 0 \\ &= \frac{\tfrac{1}{2}\ln(1+4/x)}{1/x} &&\text{downstairs: } \tfrac{0}{0} \\ \lim_{x\to\infty}\ln y &= \lim_{x\to\infty}\frac{\tfrac{1}{2}\cdot\frac{1}{1+4/x}\cdot(-4/x^{2})}{-1/x^{2}} &&\text{L'Hôpital; chain rule on } \ln(1 + 4/x) \\ &= \lim_{x\to\infty}\frac{2}{1+4/x} &&\text{cancel } -\tfrac{1}{x^{2}} \\ &= 2 &&\lim_{x\to\infty}\tfrac{4}{x} = 0 \\ \lim_{x\to\infty} y &= \boxed{e^{2}} &&y = e^{\ln y} \end{aligned}$$
:::

## Chapter 6 · Improper Integrals

### Two ways an integral breaks

An integral is improper when a limit of integration is infinite (Type 1) or the integrand blows up at a point of the interval (Type 2).

::: key
$$\underset{\text{Type 1: an infinite limit}}{\int_a^{\infty} f(x)\,dx = \lim_{b\to\infty}\int_a^{b} f(x)\,dx} \qquad\qquad \underset{\text{Type 2: } f \text{ blows up at } a}{\int_a^{b} f(x)\,dx = \lim_{t\to a^{+}}\int_t^{b} f(x)\,dx}$$
:::

Replace the bad endpoint by a letter, integrate to the letter, then take the limit; $\infty$ never goes into the antiderivative. A finite limit means the integral converges, and $\pm\infty$ or no limit means it diverges.

### The picture: a tail can have finite area

Both curves go to $0$, but only the faster drop leaves a finite area.

::: fig wave
{"x":[1,8],"y":[0,1.15],"series":[{"expr":"1/(x*x)","label":"y = 1/x²","hi":true},{"expr":"1/x","label":"y = 1/x"}],"xlabel":"x","ylabel":"y","caption":"Areas under $1/x^{2}$ and $1/x$ from $1$ onward"}

:::

$$\begin{aligned}
\int_1^{\infty}\frac{dx}{x^{2}} &= \lim_{b\to\infty}\int_1^{b} x^{-2}\,dx &&\text{rewrite as a limit} \\
&= \lim_{b\to\infty}\Big[\why{-\frac{1}{x}}{\int x^{n}\,dx = \tfrac{x^{n+1}}{n+1} + C,\ n \ne -1}\Big]_1^{b} &&\text{power rule} \\
&= \lim_{b\to\infty}\left(-\frac{1}{b} + 1\right) &&\text{upper minus lower} \\
&= \boxed{1} &&\lim_{b\to\infty}\tfrac{1}{b} = 0:\ \text{converges}
\end{aligned}$$

$$\begin{aligned}
\int_1^{\infty}\frac{dx}{x} &= \lim_{b\to\infty}\Big[\why{\ln\lvert x\rvert}{\int\tfrac{dx}{x} = \ln\lvert x\rvert + C}\Big]_1^{b} \\
&= \lim_{b\to\infty}\left(\ln b - 0\right) \\
&= \infty &&\lim_{b\to\infty}\ln b = \infty:\ \text{diverges}
\end{aligned}$$

Predict before pressing play: at $b = 12$, how far from $1$ is the first total? (It is $\frac{1}{12}$.)

::: video assets/0001-improper-tail.mp4
Area from $1$ to $b$ under $1/x^{2}$ and $1/x$
:::

### The $p$-integral rule

For $\frac{1}{x^{p}}$, the power $p$ alone decides convergence, so you read the answer off the rule instead of integrating.

::: big
$$\int_1^{\infty}\frac{dx}{x^{p}}\ \underset{\text{converges iff}}{\boxed{p > 1}}\qquad\qquad \int_0^{1}\frac{dx}{x^{p}}\ \underset{\text{converges iff}}{\boxed{p < 1}}$$
:::

$$\begin{aligned}
\int_1^{\infty}\frac{dx}{x^{p}} &= \lim_{b\to\infty}\Big[\frac{x^{1-p}}{1-p}\Big]_1^{b} &&p \neq 1 \\
&= \lim_{b\to\infty}\frac{b^{1-p} - 1}{1-p} \\
&= \frac{1}{p-1} \text{ if } p > 1 &&1 - p < 0 \text{ so } \lim_{b\to\infty} b^{1-p} = 0 \\
&= \infty \text{ if } p < 1 &&1 - p > 0 \text{ so } \lim_{b\to\infty} b^{1-p} = \infty
\end{aligned}$$

$p = 1$ diverges in both, because $\ln x$ is unbounded at both ends.

### Type 1 with parts inside: $\int_1^{\infty} x e^{-x}\,dx$

When the integrand of a Type 1 integral is a product, find the antiderivative by parts first. Then replace $\infty$ by $b$, evaluate, and take the limit.

$$\int_1^{\infty} \underbrace{x}_{u}\;\underbrace{e^{-x}\,dx}_{dv}$$

$$\boxed{\begin{aligned} u &= x & dv &= e^{-x}\,dx \\ du &= dx & v &= \why{-e^{-x}}{\int e^{ax}\,dx = \tfrac{1}{a}e^{ax} + C} \end{aligned}}$$

$$\begin{aligned}
\int x e^{-x}\,dx &= -x e^{-x} - \int (-e^{-x})\,dx &&uv - \int v\,du \\
&= -x e^{-x} - e^{-x} &&\int e^{-x}dx = -e^{-x}
\end{aligned}$$

$$\begin{aligned}
\int_1^{\infty} x e^{-x}\,dx &= \lim_{b\to\infty}\Big[-x e^{-x} - e^{-x}\Big]_1^{b} &&\text{rewrite as a limit} \\
&= \lim_{b\to\infty}\Big[(-b e^{-b} - e^{-b}) - (-e^{-1} - e^{-1})\Big] &&\text{upper minus lower} \\
&= \lim_{b\to\infty}\left(-\frac{b}{e^{b}} - \frac{1}{e^{b}}\right) + 2e^{-1} &&\text{collect the constant} \\
&= 0 - 0 + 2e^{-1} &&\lim_{b\to\infty}\tfrac{b}{e^{b}} = \lim_{b\to\infty}\tfrac{1}{e^{b}} = 0 \text{ (L'Hôpital, } \tfrac{\infty}{\infty}) \\
&= \boxed{\frac{2}{e}} &&\text{converges}
\end{aligned}$$

Write the L'Hôpital line for $\frac{b}{e^{b}}$ out; it is a graded step.

::: checkin
- *Written by Claude* Your turn: $\displaystyle\int_0^{\infty} x e^{-3x}\,dx$  ||  A comes before E, so $u = x$.

  $$\boxed{\begin{aligned} u &= x & dv &= e^{-3x}\,dx \\ du &= dx & v &= \why{-\tfrac{1}{3}e^{-3x}}{\int e^{ax}\,dx = \tfrac{1}{a}e^{ax} + C} \end{aligned}}$$

  $$\begin{aligned}
  \int x e^{-3x}\,dx &= -\tfrac{x}{3}e^{-3x} - \int \left(-\tfrac{1}{3}e^{-3x}\right)dx &&uv - \int v\,du \\
  &= -\tfrac{x}{3}e^{-3x} - \tfrac{1}{9}e^{-3x} &&\int e^{ax}\,dx = \tfrac{1}{a}e^{ax}
  \end{aligned}$$

  $$\begin{aligned}
  \int_0^{\infty} x e^{-3x}\,dx &= \lim_{b\to\infty}\Big[-\tfrac{x}{3}e^{-3x} - \tfrac{1}{9}e^{-3x}\Big]_0^{b} &&\text{rewrite as a limit} \\
  &= \lim_{b\to\infty}\left(-\tfrac{b}{3e^{3b}} - \tfrac{1}{9e^{3b}}\right) + \left(0 + \tfrac{1}{9}\right) &&\text{upper minus lower} \\
  &= 0 - 0 + \tfrac{1}{9} &&\lim_{b\to\infty}\tfrac{b}{e^{3b}} = 0 \text{ (L'Hôpital, } \tfrac{\infty}{\infty}) \\
  &= \boxed{\tfrac{1}{9}} &&\text{converges}
  \end{aligned}$$
:::

### Type 1 with a substitution inside: $\int_{e^{2}}^{\infty}\dfrac{dx}{x(\ln x)^{3}}$

When the integrand has $\ln x$ and $\frac{dx}{x}$, substitute $u$ for $\ln x$ and convert the limits to $u$. Replace $\infty$ by $b$ first, so the upper limit becomes $\ln b$.

$$\int_{e^{2}}^{\infty}\frac{1}{(\underbrace{\ln x}_{u})^{3}}\,\underbrace{\frac{dx}{x}}_{du} \qquad \underbrace{x = e^{2} \to u = 2,\quad x = b \to u = \ln b}_{\text{convert the limits}}$$

$$\begin{aligned}
\int_{e^{2}}^{\infty}\frac{dx}{x(\ln x)^{3}} &= \lim_{b\to\infty}\int_{e^{2}}^{b}\frac{dx}{x(\ln x)^{3}} &&\text{rewrite as a limit} \\
&= \lim_{b\to\infty}\int_{2}^{\ln b} u^{-3}\,du &&u = \ln x,\ du = \why{\tfrac{dx}{x}}{\tfrac{d}{dx}\ln x = \tfrac{1}{x}},\ \text{limits converted} \\
&= \lim_{b\to\infty}\Big[-\frac{1}{2u^{2}}\Big]_{2}^{\ln b} &&\text{power rule} \\
&= \lim_{b\to\infty}\left(-\frac{1}{2(\ln b)^{2}} + \frac{1}{8}\right) &&\text{upper minus lower} \\
&= \boxed{\frac{1}{8}} &&\lim_{b\to\infty}\ln b = \infty \text{ so } \lim_{b\to\infty}\tfrac{1}{(\ln b)^{2}} = 0
\end{aligned}$$

### "For what $p$ does it converge": $\int_4^{\infty}\dfrac{dx}{x(\ln x)^{p}}$

The same substitution makes it a $p$-integral at infinity, with the positive lower limit $\ln 4$.

$$\begin{aligned}
\int_4^{\infty}\frac{dx}{x(\ln x)^{p}} &= \int_{\ln 4}^{\infty}\frac{du}{u^{p}} &&u = \ln x,\ du = \tfrac{dx}{x} \\
&\text{converges exactly when } p > 1 &&p\text{-integral at } \infty
\end{aligned}$$

$$\boxed{p > 1}$$

$$\begin{aligned}
p = 1:\quad \int_{\ln 4}^{\infty}\frac{du}{u} &= \lim_{b\to\infty}(\ln b - \ln\ln 4) &&\text{show this case separately} \\
&= \infty &&\text{diverges}
\end{aligned}$$

### Type 2 with the asymptote inside: $\int_1^6 \dfrac{x}{(x^{2}-9)^{2/3}}\,dx$

Find where the bottom is $0$; if that point is inside $[a,b]$, the integral is Type 2 even though both limits are finite.

$$\int_1^6 \frac{x}{\underbrace{(x^{2}-9)^{2/3}}_{0 \text{ at } x = 3,\ \text{inside } [1,6]}}\,dx \;=\; \underbrace{\int_1^3}_{t\to 3^{-}} + \underbrace{\int_3^6}_{t\to 3^{+}}$$

Split at the asymptote; if either piece diverges, the whole integral diverges.

$$\begin{aligned}
\int \frac{x\,dx}{(x^{2}-9)^{2/3}} &= \frac{1}{2}\int u^{-2/3}\,du &&u = x^{2}-9,\ x\,dx = \tfrac{1}{2}du \\
&= \frac{1}{2}\cdot\frac{u^{1/3}}{1/3} &&\text{power rule: } -\tfrac{2}{3} + 1 = \tfrac{1}{3} \\
&= \frac{3}{2}(x^{2}-9)^{1/3} &&\text{back to } x
\end{aligned}$$

$$\begin{aligned}
\int_1^3 \frac{x\,dx}{(x^{2}-9)^{2/3}} &= \lim_{t\to 3^{-}}\Big[\tfrac{3}{2}(x^{2}-9)^{1/3}\Big]_1^{t} \\
&= \lim_{t\to 3^{-}}\tfrac{3}{2}(t^{2}-9)^{1/3} - \tfrac{3}{2}(-8)^{1/3} &&\text{upper minus lower} \\
&= 0 - \tfrac{3}{2}(-2) &&\sqrt[3]{-8} = -2 \\
&= 3
\end{aligned}$$

$$\begin{aligned}
\int_3^6 \frac{x\,dx}{(x^{2}-9)^{2/3}} &= \lim_{t\to 3^{+}}\Big[\tfrac{3}{2}(x^{2}-9)^{1/3}\Big]_t^{6} \\
&= \tfrac{3}{2}(27)^{1/3} - \lim_{t\to 3^{+}}\tfrac{3}{2}(t^{2}-9)^{1/3} \\
&= \tfrac{3}{2}\cdot 3 - 0 &&\sqrt[3]{27} = 3 \\
&= \tfrac{9}{2}
\end{aligned}$$

$$\int_1^6 \frac{x}{(x^{2}-9)^{2/3}}\,dx = 3 + \tfrac{9}{2} = \boxed{\tfrac{15}{2}}\ \text{(converges)}$$

### Type 2 at an endpoint, and the one that only looks fine

An asymptote at an endpoint takes one one-sided limit.

$$\begin{aligned}
\int_0^1\frac{dx}{\sqrt{x}} &= \lim_{t\to 0^{+}}\int_t^1 x^{-1/2}\,dx \\
&= \lim_{t\to 0^{+}}\Big[\why{2\sqrt{x}}{\int x^{n}\,dx = \tfrac{x^{n+1}}{n+1} + C}\Big]_t^{1} &&\text{power rule} \\
&= \lim_{t\to 0^{+}}\left(2 - 2\sqrt{t}\right) \\
&= \boxed{2} &&\text{converges; } p = \tfrac{1}{2} < 1
\end{aligned}$$

$\int_{-2}^{2} x^{-3}\,dx$ has its asymptote at $0$, inside the interval, so it must be split there; the right half diverges, so the whole integral diverges, even though the unsplit FTC gives $0$ by symmetry.

$$\begin{aligned}
\int_0^2 x^{-3}\,dx &= \lim_{t\to 0^{+}}\Big[\why{-\frac{1}{2x^{2}}}{\int x^{n}\,dx = \tfrac{x^{n+1}}{n+1} + C}\Big]_t^{2} &&\text{power rule} \\
&= \lim_{t\to 0^{+}}\left(-\frac{1}{8} + \frac{1}{2t^{2}}\right) &&\text{upper minus lower} \\
&= \infty &&\lim_{t\to 0^{+}}\tfrac{1}{t^{2}} = \infty:\ \text{diverges}
\end{aligned}$$

### Converge or diverge without evaluating: direct comparison

When you only need to know whether an improper integral converges and the antiderivative is hard, compare the integrand with a simpler positive function.

$$\boxed{\begin{array}{l} 0 \le f(x) \le g(x) \text{ on } [a,\infty) \\ \int_a^{\infty} g \text{ converges} \;\Rightarrow\; \int_a^{\infty} f \text{ converges} \\ \int_a^{\infty} f \text{ diverges} \;\Rightarrow\; \int_a^{\infty} g \text{ diverges} \end{array}}$$

$$\int_2^{\infty}\frac{\overbrace{\sqrt{x^{2}+3}}^{\le\, 2x}}{\underbrace{x^{4}+1}_{\ge\, x^{4}}}\,dx \qquad \text{for } x \ge 1$$

Bound it by a $p$-integral built from the highest powers. Comparison answers only "converges" or "diverges", never a value.

$$\begin{aligned}
0 \le \frac{\sqrt{x^{2}+3}}{x^{4}+1} &\le \frac{2x}{x^{4}} &&\text{top up, bottom down} \\
&= \frac{2}{x^{3}} &&p = 3 > 1 \\
\int_2^{\infty}\frac{2}{x^{3}}\,dx &\text{ converges} &&p\text{-integral} \\
\therefore\ \int_2^{\infty}\frac{\sqrt{x^{2}+3}}{x^{4}+1}\,dx &\text{ converges} &&\text{direct comparison}
\end{aligned}$$

$$\boxed{\text{converges, by comparison with } \tfrac{2}{x^{3}}}$$

### Checkpoint

*Written by Claude*

::: mcq c6a d
Which statement about $\displaystyle\int_{-1}^{1} x^{-2/3}\,dx$ is correct?
- It equals $0$, because the two halves cancel by symmetry || $x^{-2/3} = 1/(\sqrt[3]{x})^{2}$ is positive on both sides, so the halves add.
- It diverges, because $x = 0$ is a vertical asymptote inside the interval || An asymptote inside means split there; each half is a $p$-integral at $0$ with $p = \tfrac{2}{3} < 1$.
- It diverges, because $p = \tfrac{2}{3}$ is less than $1$ || $p < 1$ diverges at $\infty$; near $0$ the rule flips and $p < 1$ converges.
- It converges to $6$, because each half is a $p$-integral at $0$ with $p = \tfrac{2}{3} < 1$
why: An asymptote inside the interval means split at $0$ and take two limits. $$\begin{aligned} \int_0^{1} x^{-2/3}\,dx &= \lim_{t\to 0^{+}}\Big[\why{3x^{1/3}}{\int x^{n}\,dx = \tfrac{x^{n+1}}{n+1} + C}\Big]_t^{1} &&\text{power rule} \\ &= \lim_{t\to 0^{+}}\left(3 - 3t^{1/3}\right) = 3 &&\text{right half converges} \\ \int_{-1}^{0} x^{-2/3}\,dx &= \lim_{t\to 0^{-}}\Big[3x^{1/3}\Big]_{-1}^{t} &&\text{left half} \\ &= \lim_{t\to 0^{-}}\left(3t^{1/3} + 3\right) = 3 &&\sqrt[3]{-1} = -1 \\ \int_{-1}^{1} x^{-2/3}\,dx &= 3 + 3 = \boxed{6} &&\text{both halves converge} \end{aligned}$$
:::

*Written by Claude*

::: mcq c6b a
$\displaystyle\int_{e^{3}}^{\infty}\frac{dx}{x(\ln x)^{2}}$ equals which of these?
- $\dfrac{1}{3}$
- diverges || In $u$ it is $\int_3^{\infty} u^{-2}\,du$, a $p$-integral with $p = 2 > 1$.
- $\dfrac{1}{e^{3}}$ || $e^{3}$ was used as the lower $u$-limit instead of $\ln e^{3} = 3$.
- $-\dfrac{1}{3}$ || The bracket was evaluated lower minus upper.
why: Substitute $u = \ln x$ and convert the limits. $$\begin{aligned} \int_{e^{3}}^{\infty}\frac{dx}{x(\ln x)^{2}} &= \lim_{b\to\infty}\int_3^{\ln b} u^{-2}\,du &&du = \tfrac{dx}{x},\ \ln e^{3} = 3 \\ &= \lim_{b\to\infty}\Big[-\frac{1}{u}\Big]_3^{\ln b} &&\text{power rule} \\ &= \lim_{b\to\infty}\left(-\tfrac{1}{\ln b} + \tfrac{1}{3}\right) &&\text{upper minus lower} \\ &= \boxed{\tfrac{1}{3}} &&\lim_{b\to\infty}\tfrac{1}{\ln b} = 0 \end{aligned}$$
:::

## Chapter 7 · Which Technique

### Read the integrand, then choose

Go down this list in order and stop at the first match.

| what you see | first move | chapter |
|---|---|---|
| an antiderivative table row, maybe with $ax$ inside | write the row with $\tfrac{1}{a}$ | prereq |
| a function and its derivative, up to a constant | $u$-substitution | prereq |
| top is the derivative of the bottom | $u = \text{bottom}$, answer is $\ln\lvert\text{bottom}\rvert$ | prereq |
| two different kinds of function multiplied, $du$ absent | parts, $u$ by LIATE | 1 |
| $\ln x$ or $\tan^{-1}x$ alone | parts with $dv = dx$ | 1 |
| powers of $\sin$, $\cos$, $\tan$, $\sec$ | odd power to save, or power reduce | 2 |
| $\sqrt{a^{2}-x^{2}}$, $\sqrt{a^{2}+x^{2}}$, $\sqrt{x^{2}-a^{2}}$, or such a quadratic to a power | trig substitution | 3 |
| polynomial over a factorable polynomial, no $du$ | divide if needed, then partial fractions | 4 |
| a quadratic with a middle term under a root or alone | complete the square, then 3 or 4 | 3, 4 |
| $\infty$ as a limit, or an asymptote in the interval | write the limit first, then any of the above | 6 |

Two shapes are easy to misread. $\int\frac{x\,dx}{\sqrt{16-x^{2}}}$ has the $x\,dx$ that $u = 16 - x^{2}$ needs, so it is a $u$-substitution. $\int\frac{dx}{x^{2}+1}$ is the arctangent row, since $x^{2}+1$ does not factor.

### Drills: nine mixed integrals

Cover the right column. For each integral, say the first move out loud, then open the answer.

::: checkin
- *Written by Claude* Drill 1 $\displaystyle\int\frac{x+5}{x+2}\,dx$  ||  Top and bottom have the same degree: divide. $\frac{x+5}{x+2} = 1 + \frac{3}{x+2}$. Answer $x + 3\ln\lvert x+2\rvert + C$.
- *Written by Claude* Drill 2 $\displaystyle\int\frac{dx}{x\sqrt{4+x^{2}}}$  ||  $\sqrt{4+x^{2}}$ with no $x\,dx$ is the tangent form, so $x = 2\tan\theta$.

  $$\begin{aligned}
  x &= 2\tan\theta, \qquad dx = 2\sec^{2}\theta\,d\theta \\
  \sqrt{4+x^{2}} &= 2\sec\theta &&4 + 4\tan^{2}\theta = 4\sec^{2}\theta
  \end{aligned}$$

  $$\begin{aligned}
  \int\frac{dx}{x\sqrt{4+x^{2}}} &= \int\frac{2\sec^{2}\theta\,d\theta}{2\tan\theta\cdot 2\sec\theta} &&\text{substitute} \\
  &= \frac{1}{2}\int\frac{\sec\theta}{\tan\theta}\,d\theta &&\text{cancel } 2\sec\theta \\
  &= \frac{1}{2}\int\csc\theta\,d\theta &&\tfrac{\sec}{\tan} = \tfrac{1}{\sin} = \csc \\
  &= -\frac{1}{2}\ln\lvert\csc\theta + \cot\theta\rvert + C &&\text{the } \int\csc \text{ row} \\
  &= \boxed{-\frac{1}{2}\ln\left\lvert\frac{\sqrt{4+x^{2}}}{x} + \frac{2}{x}\right\rvert + C} &&\text{triangle: } \csc\theta = \tfrac{\sqrt{4+x^{2}}}{x},\ \cot\theta = \tfrac{2}{x}
  \end{aligned}$$
- *Written by Claude* Drill 3 $\displaystyle\int\frac{18\,dx}{(9x^{2}+1)^{2}}$  ||  $(3x)^{2}+1$ squared is the tangent form, with $3x = \tan\theta$.

  $$\begin{aligned}
  3x &= \tan\theta, \qquad dx = \tfrac{1}{3}\sec^{2}\theta\,d\theta \\
  9x^{2} + 1 &= \sec^{2}\theta &&1 + \tan^{2}\theta = \sec^{2}\theta
  \end{aligned}$$

  $$\begin{aligned}
  \int\frac{18\,dx}{(9x^{2}+1)^{2}} &= \int\frac{18\cdot\tfrac{1}{3}\sec^{2}\theta\,d\theta}{\sec^{4}\theta} &&\text{substitute} \\
  &= 6\int\cos^{2}\theta\,d\theta &&\tfrac{1}{\sec^{2}} = \cos^{2} \\
  &= 6\int\tfrac{1}{2}(1 + \cos 2\theta)\,d\theta &&\text{power reducing} \\
  &= 3\theta + \tfrac{3}{2}\sin 2\theta + C &&\int\cos 2\theta\,d\theta = \tfrac{1}{2}\sin 2\theta \\
  &= 3\theta + 3\sin\theta\cos\theta + C &&\sin 2\theta = 2\sin\theta\cos\theta \\
  &= 3\tan^{-1}(3x) + 3\cdot\frac{3x}{\sqrt{9x^{2}+1}}\cdot\frac{1}{\sqrt{9x^{2}+1}} + C &&\text{triangle: } \sin\theta = \tfrac{3x}{\sqrt{9x^{2}+1}},\ \cos\theta = \tfrac{1}{\sqrt{9x^{2}+1}} \\
  &= \boxed{3\tan^{-1}(3x) + \frac{9x}{9x^{2}+1} + C} &&\text{multiply}
  \end{aligned}$$
- *Written by Claude* Drill 4 $\displaystyle\int x^{3}\sin(x^{2})\,dx$  ||  Substitute $t = x^{2}$ first, then use parts on $t\sin t$.

  $$\begin{aligned}
  t &= x^{2}, \qquad dt = 2x\,dx \\
  x^{3}\,dx &= x^{2}\cdot x\,dx \\
  &= \tfrac{1}{2}t\,dt &&x\,dx = \tfrac{1}{2}dt
  \end{aligned}$$

  $$\boxed{\begin{aligned} u &= t & dv &= \sin t\,dt \\ du &= dt & v &= -\cos t \end{aligned}}$$

  $$\begin{aligned}
  \int x^{3}\sin(x^{2})\,dx &= \tfrac{1}{2}\int t\sin t\,dt &&\text{substitute} \\
  &= \tfrac{1}{2}\left(-t\cos t - \int(-\cos t)\,dt\right) &&uv - \int v\,du \\
  &= \tfrac{1}{2}(-t\cos t + \sin t) + C &&\int\cos t\,dt = \sin t \\
  &= \boxed{-\frac{1}{2}x^{2}\cos(x^{2}) + \frac{1}{2}\sin(x^{2}) + C} &&t = x^{2}
  \end{aligned}$$
- *Written by Claude* Drill 5 $\displaystyle\int\frac{x+6}{3x^{3}-27x}\,dx$  ||  Factor the bottom: three linear factors.

  $$\begin{aligned}
  3x^{3} - 27x &= 3x(x-3)(x+3) &&\text{factor} \\
  \frac{x+6}{3x(x-3)(x+3)} &= \frac{A}{x} + \frac{B}{x-3} + \frac{D}{x+3} &&\text{one term per linear factor}
  \end{aligned}$$

  $$\begin{aligned}
  x + 6 &= 3A(x-3)(x+3) + 3Bx(x+3) + 3Dx(x-3) &&\text{multiply by } 3x(x-3)(x+3) \\
  6 &= -27A &&\text{plug in } x = 0 \\
  A &= -\tfrac{2}{9} \\
  9 &= 54B &&\text{plug in } x = 3 \\
  B &= \tfrac{1}{6} \\
  3 &= 54D &&\text{plug in } x = -3 \\
  D &= \tfrac{1}{18}
  \end{aligned}$$

  $$\begin{aligned}
  \int\frac{x+6}{3x^{3}-27x}\,dx &= \int\left(\frac{-2/9}{x} + \frac{1/6}{x-3} + \frac{1/18}{x+3}\right)dx &&\text{the decomposition} \\
  &= \boxed{-\frac{2}{9}\ln\lvert x\rvert + \frac{1}{6}\ln\lvert x-3\rvert + \frac{1}{18}\ln\lvert x+3\rvert + C} &&\int\tfrac{1}{x} \text{ rows}
  \end{aligned}$$
- *Written by Claude* Drill 6 $\displaystyle\int(3x+1)5^{-x}\,dx$  ||  A comes before E, so $u = 3x+1$.

  $$\boxed{\begin{aligned} u &= 3x+1 & dv &= 5^{-x}\,dx \\ du &= 3\,dx & v &= -\tfrac{5^{-x}}{\ln 5} \end{aligned}}$$

  $$\begin{aligned}
  \int(3x+1)5^{-x}\,dx &= -\frac{(3x+1)5^{-x}}{\ln 5} - \int\left(-\frac{5^{-x}}{\ln 5}\right)3\,dx &&uv - \int v\,du \\
  &= -\frac{(3x+1)5^{-x}}{\ln 5} + \frac{3}{\ln 5}\int 5^{-x}\,dx &&\text{constants out} \\
  &= -\frac{(3x+1)5^{-x}}{\ln 5} - \frac{3\cdot 5^{-x}}{(\ln 5)^{2}} + C &&\int a^{-x}\,dx = -\tfrac{a^{-x}}{\ln a} \\
  &= \boxed{-5^{-x}\left[\frac{3x+1}{\ln 5} + \frac{3}{(\ln 5)^{2}}\right] + C} &&\text{factor out } -5^{-x}
  \end{aligned}$$
- *Written by Claude* Drill 7 $\displaystyle\int\frac{dx}{e^{x}\sqrt{e^{2x}-4}}$  ||  Substitute $u = e^{x}$ first; that leaves the secant form.

  $$\begin{aligned}
  u &= e^{x}, \qquad du = e^{x}\,dx \\
  dx &= \tfrac{du}{u} &&e^{x} = u \\
  u &= 2\sec\theta, \qquad du = 2\sec\theta\tan\theta\,d\theta \\
  \sqrt{u^{2}-4} &= 2\tan\theta &&\sec^{2}\theta - 1 = \tan^{2}\theta
  \end{aligned}$$

  $$\begin{aligned}
  \int\frac{dx}{e^{x}\sqrt{e^{2x}-4}} &= \int\frac{du}{u^{2}\sqrt{u^{2}-4}} &&\text{substitute } u \\
  &= \int\frac{2\sec\theta\tan\theta\,d\theta}{4\sec^{2}\theta\cdot 2\tan\theta} &&\text{substitute } \theta \\
  &= \frac{1}{4}\int\cos\theta\,d\theta &&\text{cancel; } \tfrac{1}{\sec} = \cos \\
  &= \frac{1}{4}\sin\theta + C &&\int\cos\theta\,d\theta = \sin\theta \\
  &= \frac{\sqrt{u^{2}-4}}{4u} + C &&\text{triangle: } \sin\theta = \tfrac{\sqrt{u^{2}-4}}{u} \\
  &= \boxed{\frac{\sqrt{e^{2x}-4}}{4e^{x}} + C} &&u = e^{x}
  \end{aligned}$$
- *Written by Claude* Drill 8 $\displaystyle\int\frac{2x^{2}+x+3}{x^{3}+x}\,dx$  ||  Same shape as the irreducible-quadratic example: $\frac{3}{x} + \frac{-x+1}{x^{2}+1}$. Answer $3\ln\lvert x\rvert - \tfrac{1}{2}\ln(x^{2}+1) + \tan^{-1}x + C$.
- *Written by Claude* Drill 9 $\displaystyle\int_0^2\frac{x^{3}}{x^{2}+2x+1}\,dx$  ||  Degree 3 over degree 2, so divide first.

  $$\begin{aligned}
  x^{3} &= (x-2)(x^{2}+2x+1) + (3x+2) &&\text{long division} \\
  \frac{x^{3}}{x^{2}+2x+1} &= x - 2 + \frac{3x+2}{(x+1)^{2}} &&\text{quotient} + \tfrac{\text{remainder}}{\text{bottom}} \\
  3x + 2 &= A(x+1) + B &&\text{multiply } \tfrac{A}{x+1} + \tfrac{B}{(x+1)^{2}} \text{ by } (x+1)^{2} \\
  3 &= A &&\text{match } x \text{ coefficients} \\
  -1 &= B &&\text{plug in } x = -1
  \end{aligned}$$

  $$\begin{aligned}
  \int_0^2\frac{x^{3}}{x^{2}+2x+1}\,dx &= \int_0^2\left(x - 2 + \frac{3}{x+1} - \frac{1}{(x+1)^{2}}\right)dx &&\text{the decomposition} \\
  &= \Big[\frac{x^{2}}{2} - 2x + 3\ln\lvert x+1\rvert + \frac{1}{x+1}\Big]_0^2 &&\int (x+1)^{-2}dx = -(x+1)^{-1} \\
  &= \left(2 - 4 + 3\ln 3 + \tfrac{1}{3}\right) - (3\ln 1 + 1) &&\text{upper minus lower} \\
  &= 3\ln 3 - 2 + \tfrac{1}{3} - 1 &&\ln 1 = 0 \\
  &= \boxed{3\ln 3 - \tfrac{8}{3}} &&\text{collect the constants}
  \end{aligned}$$
:::

## Chapter 8 · Practice Exam

Work all of it on paper, without notes, before opening any answer.

### Part A: true or false (5 × 2)

1. For $\displaystyle\int\frac{x^{2}\,dx}{\sqrt{x^{2}-25}}$, the right substitution is $x = 5\tan\theta$.
2. $\displaystyle\int\frac{dx}{x^{2}-9}$ requires a trig substitution.
3. $\displaystyle\int_1^{\infty}\frac{dx}{x^{3/4}}$ converges.
4. $\displaystyle\lim_{x\to 3}\frac{x-3}{x^{2}+2x-15}$ has the indeterminate form $\frac{0}{0}$.
5. $\displaystyle\int_0^{\pi/2}\tan x\,dx$ is an improper integral.

::: checkin
- *Written by Claude* A1  ||  F. $x^{2}-25$ is the form $x^{2}-a^{2}$, so $x = 5\sec\theta$. Tangent is for $a^{2}+x^{2}$.
- *Written by Claude* A2  ||  F. The bottom factors as $(x-3)(x+3)$, so partial fractions work.

  $$\begin{aligned}
  1 &= A(x+3) + B(x-3) &&\text{multiply by } (x-3)(x+3) \\
  1 &= 6A &&\text{plug in } x = 3 \\
  A &= \tfrac{1}{6} \\
  1 &= -6B &&\text{plug in } x = -3 \\
  B &= -\tfrac{1}{6} \\
  \frac{1}{x^{2}-9} &= \boxed{\frac{1/6}{x-3} - \frac{1/6}{x+3}} &&\text{the decomposition}
  \end{aligned}$$
- *Written by Claude* A3  ||  F. Here $p = \tfrac{3}{4} \le 1$, so the tail is too fat.

  $$\begin{aligned}
  \int_1^{\infty}\frac{dx}{x^{3/4}} &= \lim_{b\to\infty}\Big[4x^{1/4}\Big]_1^{b} &&\text{power rule} \\
  &= \lim_{b\to\infty}\left(4b^{1/4} - 4\right) &&\text{upper minus lower} \\
  &= \boxed{\infty} &&\text{diverges}
  \end{aligned}$$
- *Written by Claude* A4  ||  T. Top at $3$ is $0$, bottom at $3$ is $9 + 6 - 15 = 0$. (The limit itself is $\tfrac{1}{8}$ after factoring or L'Hôpital.)
- *Written by Claude* A5  ||  T. $\lim_{x\to \pi/2^{-}}\tan x = \infty$: a vertical asymptote at the endpoint $\pi/2$. (It diverges.)
:::

### Part B: multiple choice (5 × 4)

1. By LIATE, the $u$ for $\displaystyle\int x\tan^{-1}x\,dx$ is: (a) $x$ (b) $\tan^{-1}x$ (c) $x\tan^{-1}x$ (d) $x\,dx$
2. The first move for $\displaystyle\int\sin^{4}x\cos^{5}x\,dx$ is: (a) power reduce both (b) save one $\cos x$, write $\cos^{4}x$ as $(1-\sin^{2}x)^{2}$, take $\sin x$ as $u$ (c) save one $\sin x$, take $\cos x$ as $u$ (d) write $\sin^{4}x$ as $(1 - \cos^{2}x)^{2}$, take $\cos x$ as $u$
3. The substitution for $\displaystyle\int\frac{dx}{(49-x^{2})^{3/2}}$ sets $x$ to: (a) $7\sin\theta$ (b) $7\tan\theta$ (c) $7\sec\theta$ (d) $49\sin\theta$
4. The partial-fraction form of $\dfrac{x^{2}+4x+30}{(x+2)(x^{2}+9)}$ is: (a) $\dfrac{A}{x+2} + \dfrac{B}{x^{2}+9}$ (b) $\dfrac{A}{x+2} + \dfrac{Bx+D}{x^{2}+9}$ (c) $\dfrac{A}{x+2} + \dfrac{B}{x-3} + \dfrac{D}{x+3}$ (d) $\dfrac{Ax+B}{x+2} + \dfrac{D}{x^{2}+9}$
5. $\displaystyle\lim_{x\to 0^{+}} x^{3}\ln x$ equals: (a) $0$ (b) $-\infty$ (c) $1$ (d) $-\tfrac{1}{3}$

::: checkin
- *Written by Claude* B1  ||  (b). I comes before A, so $u = \tan^{-1}x$. (d) is $dv$, not $u$.

  $$\boxed{\begin{aligned} u &= \tan^{-1}x & dv &= x\,dx \\ du &= \tfrac{1}{1+x^{2}}\,dx & v &= \tfrac{x^{2}}{2} \end{aligned}}$$
- *Written by Claude* B2  ||  (b). The odd power is cosine, so one $\cos x$ is saved as $du$ for $u = \sin x$ and the rest becomes a polynomial in $\sin x$. (d) leaves no $\sin x\,dx$ for $du$.
- *Written by Claude* B3  ||  (a). $a^{2}-x^{2}$ is sine; $\sqrt{49-49\sin^{2}\theta} = 7\cos\theta$. (d) uses $49$, which is $a^{2}$, where $a$ belongs.
- *Written by Claude* B4  ||  (b). $x^{2}+9$ is irreducible, so it keeps a linear numerator. (c) wrongly factors $x^{2}+9$; (a) gives the quadratic a constant numerator, which cannot match the $x$ terms; (d) puts the linear top on the linear factor instead.

  $$\begin{aligned}
  x^{2} + 4x + 30 &= A(x^{2}+9) + (Bx+D)(x+2) &&\text{multiply by } (x+2)(x^{2}+9) \\
  26 &= 13A &&\text{plug in } x = -2 \\
  A &= 2 \\
  1 &= A + B &&\text{match } x^{2} \\
  B &= -1 \\
  30 &= 9A + 2D &&\text{match constants} \\
  D &= 6 \\
  \frac{x^{2}+4x+30}{(x+2)(x^{2}+9)} &= \boxed{\frac{2}{x+2} + \frac{-x + 6}{x^{2}+9}} &&\text{the decomposition}
  \end{aligned}$$
- *Written by Claude* B5  ||  (a). $0\cdot\infty$ form: $\frac{\ln x}{1/x^{3}}\to\frac{1/x}{-3/x^{4}}$, which simplifies to $-\frac{x^{3}}{3}\to 0$.
:::

### Part C: free response (70)

Show every step. Box the answer. Indefinite integrals need $+C$.

1. (10) $\displaystyle\int x\csc^{2}(2x)\,dx$
2. (10) $\displaystyle\int\frac{x^{2}}{(9-x^{2})^{3/2}}\,dx$
3. (10) $\displaystyle\int\frac{x+8}{x^{3}+4x}\,dx$
4. (10) $\displaystyle\int\sin^{4}x\,dx$
5. (10) Evaluate or show it diverges: $\displaystyle\int_1^{\infty}\frac{\ln x}{x^{3}}\,dx$
6. (10) $\displaystyle\lim_{x\to 0}\frac{x^{2}+\tan x}{\cos x-3}$
7. (10) For what values of $p$ does $\displaystyle\int_0^{3}\frac{dx}{x^{p}}$ converge?
8. Bonus (5) $\displaystyle\int e^{2x}\sin x\,dx$

The total is 105 with the bonus.

::: checkin
- *Written by Claude* C1 $\int x\csc^{2}(2x)\,dx$  ||  A comes before T, so $u = x$.

  $$\boxed{\begin{aligned} u &= x & dv &= \csc^{2}(2x)\,dx \\ du &= dx & v &= -\tfrac{1}{2}\cot(2x) \end{aligned}}$$

  $$\begin{aligned}
  \int x\csc^{2}(2x)\,dx &= -\frac{x}{2}\cot(2x) - \int\left(-\frac{1}{2}\cot(2x)\right)dx &&uv - \int v\,du \\
  &= -\frac{x}{2}\cot(2x) + \frac{1}{2}\cdot\frac{1}{2}\ln\lvert\sin(2x)\rvert + C &&\int\cot(ax) = \tfrac{1}{a}\ln\lvert\sin(ax)\rvert \\
  &= \boxed{-\frac{x}{2}\cot(2x) + \frac{1}{4}\ln\lvert\sin(2x)\rvert + C}
  \end{aligned}$$
:::

::: checkin
- *Written by Claude* C2 $\int\frac{x^{2}}{(9-x^{2})^{3/2}}\,dx$  ||  $9-x^{2}$ is the sine form with $a = 3$.

  $$\begin{aligned}
  x &= 3\sin\theta, \qquad dx = 3\cos\theta\,d\theta \\
  x^{2} &= 9\sin^{2}\theta \\
  (9-x^{2})^{3/2} &= (9\cos^{2}\theta)^{3/2} &&1 - \sin^{2}\theta = \cos^{2}\theta \\
  &= 27\cos^{3}\theta &&9^{3/2} = 27
  \end{aligned}$$

  $$\begin{aligned}
  \int\frac{x^{2}\,dx}{(9-x^{2})^{3/2}} &= \int\frac{9\sin^{2}\theta\cdot 3\cos\theta\,d\theta}{27\cos^{3}\theta} &&\text{substitute} \\
  &= \int\frac{\sin^{2}\theta}{\cos^{2}\theta}\,d\theta &&\text{cancel } 27 \text{ and } \cos\theta \\
  &= \int\tan^{2}\theta\,d\theta &&\tfrac{\sin}{\cos} = \tan \\
  &= \int(\sec^{2}\theta - 1)\,d\theta &&\tan^{2} = \sec^{2} - 1 \\
  &= \tan\theta - \theta + C &&\text{table rows} \\
  &= \boxed{\frac{x}{\sqrt{9-x^{2}}} - \sin^{-1}\!\left(\frac{x}{3}\right) + C} &&\text{triangle: opp } x,\ \text{adj } \sqrt{9-x^{2}},\ \text{hyp } 3
  \end{aligned}$$
:::

::: checkin
- *Written by Claude* C3 $\int\frac{x+8}{x^{3}+4x}\,dx$  ||  $x^{3}+4x = x(x^{2}+4)$. Form $\frac{A}{x} + \frac{Bx+D}{x^{2}+4}$.
  $$\begin{aligned}
  x + 8 &= A(x^{2}+4) + (Bx+D)x &&\text{clear denominators} \\
  8 &= 4A &&\text{plug in } x = 0 \\
  A &= 2 \\
  0 &= A + B &&x^{2} \text{ coefficients} \\
  B &= -2 \\
  1 &= D &&x \text{ coefficients} \\
  \int\frac{x+8}{x^{3}+4x}\,dx &= \int\left(\frac{2}{x} - \frac{2x}{x^{2}+4} + \frac{1}{x^{2}+4}\right)dx \\
  &= \boxed{2\ln\lvert x\rvert - \ln(x^{2}+4) + \tfrac{1}{2}\tan^{-1}\tfrac{x}{2} + C} &&\int\tfrac{2x}{x^{2}+4} = \ln(x^{2}+4),\ \int\tfrac{dx}{x^{2}+a^{2}} = \tfrac{1}{a}\tan^{-1}\tfrac{x}{a}
  \end{aligned}$$
:::

::: checkin
- *Written by Claude* C4 $\int\sin^{4}x\,dx$  ||  Both-even case: power reduce twice.
  $$\begin{aligned}
  \sin^{4}x &= \left(\tfrac{1}{2}(1-\cos 2x)\right)^{2} &&\text{power reducing} \\
  &= \tfrac{1}{4}\left(1 - 2\cos 2x + \cos^{2}2x\right) &&\text{expand} \\
  &= \tfrac{1}{4}\left(1 - 2\cos 2x + \tfrac{1}{2}(1 + \cos 4x)\right) &&\text{power reduce } \cos^{2}2x \\
  &= \tfrac{3}{8} - \tfrac{1}{2}\cos 2x + \tfrac{1}{8}\cos 4x &&\text{collect} \\
  \int\sin^{4}x\,dx &= \boxed{\frac{3x}{8} - \frac{\sin 2x}{4} + \frac{\sin 4x}{32} + C} &&\int\cos(ax) = \tfrac{1}{a}\sin(ax)
  \end{aligned}$$
:::

::: checkin
- *Written by Claude* C5 $\int_1^{\infty}\frac{\ln x}{x^{3}}\,dx$  ||  Type 1. Inside, L comes before A, so $u = \ln x$.

  $$\boxed{\begin{aligned} u &= \ln x & dv &= x^{-3}\,dx \\ du &= \tfrac{dx}{x} & v &= -\tfrac{1}{2x^{2}} \end{aligned}}$$

  $$\begin{aligned}
  \int\frac{\ln x}{x^{3}}\,dx &= -\frac{\ln x}{2x^{2}} + \int\frac{1}{2x^{3}}\,dx &&uv - \int v\,du \\
  &= -\frac{\ln x}{2x^{2}} - \frac{1}{4x^{2}} \\
  \int_1^{\infty}\frac{\ln x}{x^{3}}\,dx &= \lim_{b\to\infty}\Big[-\frac{\ln x}{2x^{2}} - \frac{1}{4x^{2}}\Big]_1^{b} &&\text{rewrite as a limit} \\
  &= \lim_{b\to\infty}\left(-\frac{\ln b}{2b^{2}} - \frac{1}{4b^{2}}\right) - \left(0 - \frac{1}{4}\right) &&\text{upper minus lower} \\
  &= -0 - 0 + \frac{1}{4} &&\lim_{b\to\infty}\tfrac{\ln b}{b^{2}} = \lim_{b\to\infty}\tfrac{1/b}{2b} = 0 \\
  &= \boxed{\tfrac{1}{4}}\ \text{(converges)}
  \end{aligned}$$
:::

::: checkin
- *Written by Claude* C6 $\lim_{x\to 0}\frac{x^{2}+\tan x}{\cos x-3}$  ||  Plug in first. The form is $\frac{0}{-2}$, not indeterminate, so L'Hôpital does not apply.

  $$\begin{aligned}
  \lim_{x\to 0}\frac{x^{2}+\tan x}{\cos x-3} &= \frac{0 + 0}{1 - 3} &&\text{plug in} \\
  &= \frac{0}{-2} &&\text{not indeterminate} \\
  &= \boxed{0}
  \end{aligned}$$

  Full credit is the line "$\frac{0}{-2}$, not indeterminate, limit $= 0$".
:::

::: checkin
- *Written by Claude* C7 for what $p$ does $\int_0^{3}\frac{dx}{x^{p}}$ converge  ||  Type 2 at $0$. For $p \ne 1$:
  $$\begin{aligned}
  \int_0^{3} x^{-p}\,dx &= \lim_{t\to 0^{+}}\Big[\frac{x^{1-p}}{1-p}\Big]_t^{3} \\
  &= \lim_{t\to 0^{+}}\frac{3^{1-p} - t^{1-p}}{1-p} &&\text{upper minus lower} \\
  &= \frac{3^{1-p}}{1-p} \text{ if } p < 1 &&1 - p > 0 \text{ so } \lim_{t\to 0^{+}} t^{1-p} = 0 \\
  &= \infty \text{ if } p > 1 &&1 - p < 0 \text{ so } \lim_{t\to 0^{+}} t^{1-p} = \infty
  \end{aligned}$$
  For $p = 1$ it diverges too.

  $$\begin{aligned}
  \int_0^{3}\frac{dx}{x} &= \lim_{t\to 0^{+}}(\ln 3 - \ln t) &&\text{upper minus lower} \\
  &= \infty &&\text{diverges}
  \end{aligned}$$

  $$\boxed{p < 1}$$
:::

::: checkin
- *Written by Claude* Bonus $\int e^{2x}\sin x\,dx$  ||  The loop: two rounds of parts bring $I$ back.

  Round 1, with $u$ trig:

  $$\boxed{\begin{aligned} u &= \sin x & dv &= e^{2x}\,dx \\ du &= \cos x\,dx & v &= \tfrac{1}{2}e^{2x} \end{aligned}}$$

  $$\begin{aligned}
  I &= \int e^{2x}\sin x\,dx \\
  &= \tfrac{1}{2}e^{2x}\sin x - \tfrac{1}{2}\int e^{2x}\cos x\,dx &&uv - \int v\,du
  \end{aligned}$$

  Round 2, with $u$ trig again:

  $$\boxed{\begin{aligned} u &= \cos x & dv &= e^{2x}\,dx \\ du &= -\sin x\,dx & v &= \tfrac{1}{2}e^{2x} \end{aligned}}$$

  $$\begin{aligned}
  \int e^{2x}\cos x\,dx &= \tfrac{1}{2}e^{2x}\cos x - \int \tfrac{1}{2}e^{2x}(-\sin x)\,dx &&uv - \int v\,du \\
  &= \tfrac{1}{2}e^{2x}\cos x + \tfrac{1}{2}I &&\text{the original integral is back}
  \end{aligned}$$

  $$\begin{aligned}
  I &= \tfrac{1}{2}e^{2x}\sin x - \tfrac{1}{2}\left(\tfrac{1}{2}e^{2x}\cos x + \tfrac{1}{2}I\right) &&\text{substitute round 2} \\
  I &= \tfrac{1}{2}e^{2x}\sin x - \tfrac{1}{4}e^{2x}\cos x - \tfrac{1}{4}I &&\text{distribute} \\
  \tfrac{5}{4}I &= \tfrac{1}{2}e^{2x}\sin x - \tfrac{1}{4}e^{2x}\cos x &&\text{add } \tfrac{1}{4}I \text{ to both sides} \\
  I &= \boxed{\tfrac{1}{5}e^{2x}(2\sin x - \cos x) + C} &&\text{multiply by } \tfrac{4}{5},\ \text{add } C
  \end{aligned}$$
:::

## Chapter 9 · Last Night Cheat Sheet

::: sheet
::: group Parts
::: key
$$\int u\,dv = uv - \int v\,du$$
:::

$$\underset{\text{Log}}{\mathrm{L}}\quad\underset{\text{Inverse trig}}{\mathrm{I}}\quad\underset{\text{Algebraic}}{\mathrm{A}}\quad\underset{\text{Trig}}{\mathrm{T}}\quad\underset{\text{Exponential}}{\mathrm{E}}$$

$$\begin{aligned}
&+,\ -,\ + &&\text{polynomial } u\text{: table} \\
&\int e^{x}\sin x,\ \int e^{x}\cos x,\ \int\csc^{3}x &&\text{loop twice, solve for } I \\
\int_a^b u\,dv &= \Big[uv\Big]_a^b - \int_a^b v\,du &&\text{definite: no } +C
\end{aligned}$$
:::

::: group Trig integrals
$$\begin{aligned}
\sin^{2}x + \cos^{2}x &= 1 &&\text{Pythagorean} \\
1 + \tan^{2}x &= \sec^{2}x &&\text{Pythagorean} \\
1 + \cot^{2}x &= \csc^{2}x &&\text{Pythagorean} \\
\sin^{2}x &= \tfrac{1}{2}(1 - \cos 2x) &&\text{power reducing} \\
\cos^{2}x &= \tfrac{1}{2}(1 + \cos 2x) &&\text{power reducing} \\
\sin 2x &= 2\sin x\cos x &&\text{double angle}
\end{aligned}$$

| powers | save as $du$ | $u$ |
|---|---|---|
| $\sin$ or $\cos$ odd | one of the odd | the other |
| both even | nothing: power reduce | none |
| $\sec$ even | $\sec^{2}x$ | $\tan x$ |
| $\tan$ odd | $\sec x\tan x$ | $\sec x$ |

$$\begin{aligned}
(\cot x)' &= -\csc^{2}x &&\text{cot, csc: same, with a minus} \\
(\csc x)' &= -\csc x\cot x
\end{aligned}$$
:::

::: group Trig substitution
::: big
$$\underset{x \,=\, a\sin\theta}{a^{2}-x^{2}}\qquad\underset{x \,=\, a\tan\theta}{a^{2}+x^{2}}\qquad\underset{x \,=\, a\sec\theta}{x^{2}-a^{2}}$$
:::

| form | $dx$ | root becomes |
|---|---|---|
| $a^{2} - x^{2}$ | $a\cos\theta\,d\theta$ | $a\cos\theta$ |
| $a^{2} + x^{2}$ | $a\sec^{2}\theta\,d\theta$ | $a\sec\theta$ |
| $x^{2} - a^{2}$ | $a\sec\theta\tan\theta\,d\theta$ | $a\tan\theta$ |

$$\begin{aligned}
\sin 2\theta &= 2\sin\theta\cos\theta &&\text{rewrite before the triangle} \\
\theta &= \sin^{-1}\tfrac{x}{a} &&\text{a bare } \theta \\
x^{2} + bx + c &= \left(x + \tfrac{b}{2}\right)^{2} + c - \tfrac{b^{2}}{4} &&\text{middle term}
\end{aligned}$$
:::

::: group Partial fractions
$$\begin{aligned}
\frac{\text{top}}{\text{bottom}} &= \text{quotient} + \frac{\text{remainder}}{\text{bottom}} &&\deg\text{top} \ge \deg\text{bottom} \\
(x-r) &\to \frac{A}{x-r} &&\text{clear, plug in roots} \\
(x-r)^{2} &\to \frac{A}{x-r} + \frac{B}{(x-r)^{2}} &&\text{one per power} \\
x^{2}+bx+c &\to \frac{Ax+B}{x^{2}+bx+c} &&\text{irreducible: match coefficients} \\
\int\frac{2x\,dx}{x^{2}+a^{2}} &= \ln(x^{2}+a^{2}) \\
\int\frac{dx}{x^{2}+a^{2}} &= \frac{1}{a}\tan^{-1}\frac{x}{a}
\end{aligned}$$
:::

::: group L'Hôpital
::: key
$$\lim\frac{f}{g} = \lim\frac{f'}{g'} \qquad \tfrac{0}{0},\ \tfrac{\infty}{\infty}\ \text{only}$$
:::

$$\begin{aligned}
f\cdot g &= \frac{f}{1/g} &&0\cdot\infty \\
\frac{1}{a} - \frac{1}{b} &= \frac{b-a}{ab} &&\infty - \infty\text{: one fraction} \\
\ln y &= g\ln f,\quad \lim y = e^{L} &&1^{\infty},\ 0^{0},\ \infty^{0} \\
\lim_{x\to\infty}\left(1+\frac{a}{x}\right)^{bx} &= e^{ab} \\
\frac{0}{-1} &= 0 &&\text{plug in first: not indeterminate}
\end{aligned}$$
:::

::: group Improper integrals
$$\begin{aligned}
\int_a^{\infty} f &= \lim_{b\to\infty}\int_a^{b} f &&\text{Type 1} \\
\int_a^{b} f &= \lim_{t\to a^{+}}\int_t^{b} f &&\text{Type 2} \\
\int_a^{b} f &= \int_a^{c} f + \int_c^{b} f &&\text{asymptote at } c\text{: both converge}
\end{aligned}$$

::: key
$$\int_1^{\infty}\frac{dx}{x^{p}}\ \underset{\text{converges iff}}{p > 1}\qquad \int_0^{1}\frac{dx}{x^{p}}\ \underset{\text{converges iff}}{p < 1}$$
:::

$$\begin{aligned}
\lim_{b\to\infty}\frac{b}{e^{b}} &= 0 \\
\lim_{b\to\infty}\frac{\ln b}{b} &= 0 &&\text{inside limits}
\end{aligned}$$

$$\begin{aligned}
0 \le f \le g,\ \int g \text{ converges} &\;\Rightarrow\; \int f \text{ converges} &&\text{comparison: yes or no only}
\end{aligned}$$

::: callout
wrong: $\dfrac{1}{\infty} = 0$, $e^{\infty}$
right: $\displaystyle\lim_{b\to\infty}\frac{1}{b} = 0$
:::
:::
:::

::: callout
wrong: $\int f(x)$
right: $\int f(x)\,dx$
$+C$ on indefinite, never on definite · $\ln\lvert\ \rvert$ · $u$, $du$ lines written · no $x$ and $u$ on one line · exact values · box the answer.
:::

## Quiz

Six fresh items, mixing chapters. None says which technique to use.

::: quiz
topics: integration by parts, trig integrals, trig substitution, partial fractions, L'Hôpital's rule, improper integrals

*Written by Claude*

::: mcq q1 b
$\displaystyle\int x\sin(2x)\,dx$ equals which of these?
- $-\dfrac{x}{2}\cos(2x) - \dfrac{1}{4}\sin(2x) + C$ || One of the two minus signs was lost: $-\int\left(-\tfrac{1}{2}\cos 2x\right)dx = +\tfrac{1}{4}\sin 2x$.
- $-\dfrac{x}{2}\cos(2x) + \dfrac{1}{4}\sin(2x) + C$
- $-\dfrac{x^{2}}{4}\cos(2x) + C$ || This multiplies the antiderivatives of the two factors, which is not a rule.
- $-2x\cos(2x) + 4\sin(2x) + C$ || This multiplies by $2$; $\int\sin(2x)\,dx = -\tfrac{1}{2}\cos(2x)$ divides by it.
why: A comes before T, so $u = x$. $$\boxed{\begin{aligned} u &= x & dv &= \sin 2x\,dx \\ du &= dx & v &= -\tfrac{1}{2}\cos 2x \end{aligned}}$$ $$\begin{aligned} \int x\sin(2x)\,dx &= -\tfrac{x}{2}\cos 2x - \int\left(-\tfrac{1}{2}\cos 2x\right)dx &&uv - \int v\,du \\ &= \boxed{-\tfrac{x}{2}\cos 2x + \tfrac{1}{4}\sin 2x + C} &&\int\cos(ax)\,dx = \tfrac{1}{a}\sin(ax) \end{aligned}$$
:::

*Written by Claude*

::: mcq q2 d
$\displaystyle\int \tan^{4}x\sec^{2}x\,dx$ equals which of these?
- $4\tan^{3}x\sec^{2}x + C$ || The power rule was run backwards: $u^{4}$ was differentiated to $4u^{3}$ instead of integrated.
- $\dfrac{\tan^{5}x}{5} + \dfrac{\tan^{7}x}{7} + C$ || $\sec^{2}x$ was converted to $1 + \tan^{2}x$ though it was already the $du$.
- $\dfrac{\tan^{5}x}{5}\sec^{2}x + C$ || $\sec^{2}x$ was kept after it was used up as $du$.
- $\dfrac{\tan^{5}x}{5} + C$
why: $\sec^{2}x\,dx$ is already $du$ for $u = \tan x$. $$\begin{aligned} \int \tan^{4}x\sec^{2}x\,dx &= \int u^{4}\,du &&u = \tan x,\ du = \sec^{2}x\,dx \\ &= \tfrac{u^{5}}{5} + C &&\text{power rule} \\ &= \boxed{\tfrac{\tan^{5}x}{5} + C} &&u = \tan x \end{aligned}$$
:::

*Written by Claude*

::: mcq q3 c
For $\displaystyle\int\frac{\sqrt{x^{2}-16}}{x}\,dx$, which substitution is right, and what does the root become?
- $x = 4\tan\theta$, and $\sqrt{x^{2}-16}$ becomes $4\sec\theta$ || Tangent is for $16 + x^{2}$; here it gives $16\tan^{2}\theta - 16$, not a square.
- $x = 4\sin\theta$, and $\sqrt{x^{2}-16}$ becomes $4\cos\theta$ || $16\sin^{2}\theta - 16 = -16\cos^{2}\theta$ is negative under the root.
- $x = 4\sec\theta$, and $\sqrt{x^{2}-16}$ becomes $4\tan\theta$
- $x = 16\sec\theta$, and $\sqrt{x^{2}-16}$ becomes $16\tan\theta$ || This uses $16$, which is $a^{2}$; the substitution uses $a = 4$.
why: $x^{2}-16$ is $x^{2}-a^{2}$ with $a = 4$, so secant. $$\begin{aligned} x &= 4\sec\theta \\ \sqrt{x^{2}-16} &= \sqrt{16\sec^{2}\theta - 16} &&\text{substitute} \\ &= \sqrt{16\tan^{2}\theta} &&\sec^{2}\theta - 1 = \tan^{2}\theta \\ &= \boxed{4\tan\theta} &&\text{no root left} \end{aligned}$$
:::

*Written by Claude*

::: mcq q4 a
$\displaystyle\int_3^{\infty}\frac{dx}{x^{2}-4}$ equals which of these?
- $\tfrac{1}{4}\ln 5$
- diverges, because the antiderivative contains $\ln$ || The $\ln$ is of a ratio that tends to $1$, so it tends to $0$.
- $\ln 5$ || The $\tfrac{1}{4}$ from $A$ and $B$ was dropped.
- $-\tfrac{1}{4}\ln 5$ || The signs of $A$ and $B$ were swapped; $A$ is $+\tfrac{1}{4}$.
why: The bottom is $(x-2)(x+2)$, two linear factors. $$\begin{aligned} 1 &= A(x+2) + B(x-2) &&\text{multiply by } (x-2)(x+2) \\ 1 &= 4A &&\text{plug in } x = 2 \\ A &= \tfrac{1}{4} \\ 1 &= -4B &&\text{plug in } x = -2 \\ B &= -\tfrac{1}{4} \end{aligned}$$ $$\begin{aligned} \int_3^{\infty}\frac{dx}{x^{2}-4} &= \lim_{b\to\infty}\Big[\tfrac{1}{4}\ln\lvert x-2\rvert - \tfrac{1}{4}\ln\lvert x+2\rvert\Big]_3^{b} &&\int\tfrac{1}{x} \text{ rows} \\ &= \lim_{b\to\infty}\Big[\tfrac{1}{4}\ln\frac{x-2}{x+2}\Big]_3^{b} &&\ln a - \ln b = \ln\tfrac{a}{b} \\ &= \lim_{b\to\infty}\tfrac{1}{4}\ln\frac{b-2}{b+2} - \tfrac{1}{4}\ln\tfrac{1}{5} &&\text{upper minus lower} \\ &= 0 + \tfrac{1}{4}\ln 5 &&\lim_{b\to\infty}\tfrac{b-2}{b+2} = 1,\ -\ln\tfrac{1}{5} = \ln 5 \\ &= \boxed{\tfrac{1}{4}\ln 5} \end{aligned}$$
:::

*Written by Claude*

::: mcq q5 d
$\displaystyle\lim_{x\to 0^{+}}(1+2x)^{1/x}$ equals which of these?
- $1$ || $1^{\infty}$ was read as $1$; the base is above $1$ while the exponent grows.
- $\infty$ || The exponent alone going to $\infty$ does not decide the limit.
- $e$ || The chain-rule factor $2$ was dropped: the derivative of $\ln(1+2x)$ is $\tfrac{2}{1+2x}$.
- $e^{2}$
why: $1^{\infty}$ form, so take the logarithm. $$\begin{aligned} \ln y &= \frac{\ln(1+2x)}{x} &&\ln a^{b} = b\ln a;\ \tfrac{0}{0} \\ \lim_{x\to 0^{+}}\ln y &= \lim_{x\to 0^{+}}\frac{2/(1+2x)}{1} &&\text{L'Hôpital; chain rule on top} \\ &= 2 &&\text{plug in } 0 \\ \lim_{x\to 0^{+}} y &= \boxed{e^{2}} &&y = e^{\ln y} \end{aligned}$$
:::

*Written by Claude*

::: mcq q6 b
$\displaystyle\int_0^{3}\frac{dx}{(x-1)^{2}}$ equals which of these?
- $-\tfrac{3}{2}$ || This is the FTC straight across the asymptote at $x = 1$, which is not allowed.
- diverges
- $\tfrac{3}{2}$ || This is the straight-across FTC with the sign flipped; the asymptote at $x = 1$ forbids it.
- converges, because $\tfrac{1}{(x-1)^{2}}$ is positive and bounded on $[0,3]$ || It is not bounded: it goes to $\infty$ at $x = 1$.
why: $x = 1$ is a vertical asymptote inside $[0,3]$, so split there and test the right half. $$\begin{aligned} \int_1^{3}(x-1)^{-2}dx &= \lim_{t\to 1^{+}}\Big[-\tfrac{1}{x-1}\Big]_t^{3} \\ &= \lim_{t\to 1^{+}}\left(-\tfrac{1}{2} + \tfrac{1}{t-1}\right) \\ &= \infty \end{aligned}$$
:::
:::
