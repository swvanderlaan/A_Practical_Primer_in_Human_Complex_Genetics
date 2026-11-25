#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_student_code.py

Extract the code a student is asked to run from one chapter (.qmd) of
'A Practical Primer in Human Complex Genetics', so the exercises can be tested
end-to-end. Code blocks labelled "Terminal" go to a Bash script and code blocks
labelled "R" go to an R script, both in the order they appear in the chapter.
Code that only builds the book (hidden chunks reading from data/...) is skipped.

Output files are written next to the --input file, date-prefixed, with an
'_annotated' suffix (e.g. 20261124_03_2_gwas_basics_sample_qc_cocalc_annotated.sh),
unless --output is given. A date-prefixed log file is written in the same place.

Usage:
    python3 scripts/extract_student_code.py --input 03_2_gwas_basics_sample_qc_cocalc.qmd
    python3 scripts/extract_student_code.py --input 03_2_gwas_basics_sample_qc_cocalc.qmd --output ~/primer_test/ch03_2

MIT License

Copyright (c) 2026 Sander W. van der Laan | s.w.vanderlaan [at] gmail [dot] com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

VERSION_NAME = "extract_student_code"
VERSION = "1.0.0"
VERSION_DATE = "2026-11-24"

import argparse
import datetime
import logging
import os
import re
import sys

# matches a fenced block header, e.g. ```{.bash filename="Terminal"} or ```{r, eval = FALSE}
FENCE_OPEN = re.compile(r'^```\{(?P<hdr>[^}]*)\}\s*$')
FENCE_CLOSE = re.compile(r'^```\s*$')


def parse_args():
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(
        prog=VERSION_NAME,
        description=f"{VERSION_NAME} v{VERSION} ({VERSION_DATE}): extract Terminal and R "
                    "code blocks from a primer chapter into runnable .sh and .R files.")
    p.add_argument("--input", required=True, help="Chapter file (.qmd).")
    p.add_argument("--output", default=None,
                   help="Output basename (without extension). Default: "
                        "<input dir>/<date>_<input name>_annotated")
    p.add_argument("--version", action="version", version=f"{VERSION_NAME} v{VERSION} ({VERSION_DATE})")
    return p.parse_args()


def setup_logging(log_path):
    """Log to file and to the console."""
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)])


def classify(header, body):
    """
    Decide what a code block is.

    Returns 'terminal', 'r' or None (skip). Hidden chunks (echo/include = FALSE)
    only build the book and are skipped; so are 'Output' blocks.
    """
    if 'filename="Output"' in header:
        return None
    if 'filename="Terminal"' in header or re.match(r'\s*(bash|sh)\b', header):
        return 'terminal'
    is_r = header.startswith('.r') or re.match(r'\s*r\b', header)
    if is_r:
        hidden = re.search(r'(echo|include)\s*=\s*(FALSE|F)\b', header) or \
                 re.search(r'#\|\s*(echo|include):\s*false', body)
        return None if hidden else 'r'
    return None


def extract(path):
    """Walk the chapter and return lists of (line number, code) for Terminal and R blocks."""
    terminal, rcode = [], []
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    i = 0
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i].strip())
        if not m:
            i += 1
            continue
        start = i + 1
        j = start
        while j < len(lines) and not FENCE_CLOSE.match(lines[j].strip()):
            j += 1
        body = "\n".join(lines[start:j])
        kind = classify(m.group("hdr").strip(), body)
        # drop Quarto cell options ('#| ...') from the extracted code
        code = "\n".join(l for l in lines[start:j] if not l.lstrip().startswith("#|")).strip("\n")
        if kind == 'terminal':
            terminal.append((start, code))
        elif kind == 'r':
            rcode.append((start, code))
        i = j + 1
    return terminal, rcode


def write_script(path, blocks, shebang, source):
    """Write blocks to a script, each preceded by a comment pointing to the chapter line."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(shebang + "\n")
        fh.write(f"# Extracted from {source} by {VERSION_NAME} v{VERSION} on {datetime.date.today()}\n\n")
        for lineno, code in blocks:
            fh.write(f"# ---- {source}, line {lineno}\n{code}\n\n")


def main():
    args = parse_args()
    inp = os.path.abspath(os.path.expanduser(args.input))
    if not os.path.isfile(inp):
        sys.exit(f"ERROR: input file not found: {inp}")
    today = datetime.date.today().strftime("%Y%m%d")
    stem = os.path.splitext(os.path.basename(inp))[0]
    in_dir = os.path.dirname(inp)
    out_base = os.path.expanduser(args.output) if args.output else \
        os.path.join(in_dir, f"{today}_{stem}_annotated")
    # log file lives next to the input file, date-prefixed
    setup_logging(os.path.join(in_dir, f"{today}_{stem}_{VERSION_NAME}.log"))
    logging.info("%s v%s (%s)", VERSION_NAME, VERSION, VERSION_DATE)
    logging.info("Input: %s", inp)

    terminal, rcode = extract(inp)
    if terminal:
        write_script(out_base + ".sh", terminal, "#!/usr/bin/env bash", os.path.basename(inp))
        logging.info("Wrote %d Terminal blocks to %s.sh", len(terminal), out_base)
    if rcode:
        write_script(out_base + ".R", rcode, "#!/usr/bin/env Rscript", os.path.basename(inp))
        logging.info("Wrote %d R blocks to %s.R", len(rcode), out_base)
    if not terminal and not rcode:
        logging.warning("No student code found in %s", inp)


if __name__ == "__main__":
    main()
