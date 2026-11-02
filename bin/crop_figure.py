#!/usr/bin/env python3
"""Crop an official problem's figure from its source PDF page into the lesson's assets (the real image, not a redraw).

  crop_figure.py --pdf sources/exams2/fa18-kj-e2.pdf --page 6 --box 0.08,0.42,0.92,0.80 --out lessons/assets/0010-fa18-p3b.png
  crop_figure.py --pdf … --page 6 --preview          # whole page at 100 dpi with a 10% grid, to pick the box

--box is left,top,right,bottom as fractions of the page (0..1). Renders at 200 dpi with pdftoppm, crops, trims to a
white margin, and writes a PNG. Look at the result before using it: the whole figure and its labels, nothing else.
"""
import argparse, os, subprocess, sys, tempfile


def render(pdf, page, dpi, out_prefix):
    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(dpi), "-png", "-singlefile", pdf, out_prefix], check=True)
    return out_prefix + ".png"


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--pdf", required=True)
    a.add_argument("--page", type=int, required=True, help="1-based PDF page")
    a.add_argument("--box", help="left,top,right,bottom fractions")
    a.add_argument("--out")
    a.add_argument("--dpi", type=int, default=200)
    a.add_argument("--preview", action="store_true")
    o = a.parse_args(argv)
    with tempfile.TemporaryDirectory() as tmp:
        if o.preview:
            png = render(o.pdf, o.page, 100, os.path.join(tmp, "p"))
            out = o.out or f"/tmp/crop-preview-p{o.page}.png"
            grid = ",".join(f"drawgrid=w=iw/10:h=ih/10:t=1:c=red@0.5" for _ in range(1))
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", png, "-vf", grid, out], check=True)
            print(out)
            return 0
        if not (o.box and o.out):
            a.error("--box and --out are required (or --preview)")
        l, t, r, b = (float(x) for x in o.box.split(","))
        if not (0 <= l < r <= 1 and 0 <= t < b <= 1):
            a.error("--box must be left<right, top<bottom, all within 0..1")
        png = render(o.pdf, o.page, o.dpi, os.path.join(tmp, "p"))
        crop = f"crop=iw*{r - l}:ih*{b - t}:iw*{l}:ih*{t}"
        os.makedirs(os.path.dirname(os.path.abspath(o.out)), exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", png, "-vf", crop, o.out], check=True)
        print(o.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
