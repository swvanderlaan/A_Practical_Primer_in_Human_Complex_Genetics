#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_student_code.py

Extract the code a student is asked to run from one chapter (.qmd) of
'A Practical Primer in Human Complex Genetics', so the exercises can be tested
end-to-end. Code blocks labelled "Terminal" go to a Bash script and code blocks
labelled "R" go to an R script, both in the order they appear in the chapter.
Code that only builds the book (hidden chunks reading from data/...) is skipped; hidden
answers to exercises (hidden, not run for the book, not reading data/) are included.

Output files are written next to the --input file, date-prefixed, with an
'_annotated' suffix (e.g. 20261124_03_2_gwas_basics_sample_qc_cocalc_annotated.sh),
unless --output is given. A date-prefixed log file is written in the same place.

With --combined, all blocks are also written, in chapter order, to one R script
(<basename>_combined.R). Terminal blocks are run from R with system2("bash"), so
the order of Terminal and R steps is kept and R objects persist between steps.
A Terminal block that only does 'cd <dir>' becomes setwd("<dir>"). The script
stops at the first failing step and reports the chapter line. A Terminal step that
the book expects to fail (the next code block is an Output block starting with
'Error') is reported as an expected error and the script continues.

The CoCalc chapters read the course data from ~/data/shared. In the combined
script that path is replaced by --data-dir (default: the data/ folder next to the
chapter, i.e. the repository's own data folder), so no link in $HOME is needed.

Usage:
    python3 scripts/extract_student_code.py --input 03_2_gwas_basics_sample_qc_cocalc.qmd --combined
    python3 scripts/extract_student_code.py --input 03_2_gwas_basics_sample_qc_cocalc.qmd --combined \
        --output primer_test/03_2_gwas_basics_sample_qc_cocalc --data-dir data
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
VERSION = "1.4.0"
VERSION_DATE = "2026-11-26"

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
    p.add_argument("--combined", action="store_true",
                   help="Also write one R script with all Terminal and R steps in chapter order.")
    p.add_argument("--data-dir", default=None,
                   help="Folder that replaces ~/data/shared in the combined script. "
                        "Default: the data/ folder next to --input.")
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
    if 'filename="Terminal"' in header:
        return 'terminal'
    if re.match(r'\s*(bash|sh)\b', header):
        # an executable bash chunk with echo/include = FALSE only builds the book
        hidden = re.search(r'(echo|include)\s*=\s*(FALSE|F)\b', header) or \
                 re.search(r'#\|\s*(echo|include):\s*false', body)
        return None if hidden else 'terminal'
    is_r = header.startswith('.r') or re.match(r'\s*r\b', header)
    if is_r:
        hidden = re.search(r'(echo|include)\s*=\s*(FALSE|F)\b', header) or \
                 re.search(r'#\|\s*(echo|include):\s*false', body)
        if not hidden:
            return 'r'
        # A hidden chunk that is not run for the book (eval = FALSE) and does not read the
        # book's own data/ folder is the answer to an exercise: a student needs it too.
        not_run = re.search(r'eval\s*=\s*(FALSE|F)\b', header)
        reads_book_data = re.search(r'["\']data/', body)
        return 'r' if (not_run and not reads_book_data) else None
    return None


def extract(path):
    """Walk the chapter and return lists of (line number, code) for Terminal and R blocks."""
    terminal, rcode, ordered = [], [], []
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
        if kind:
            ordered.append([kind, start, code, False])
        elif 'filename="Output"' in m.group("hdr") and body.lstrip().startswith("Error") \
                and ordered and ordered[-1][0] == 'terminal':
            # the book shows this error on purpose: the previous Terminal step is expected to fail
            ordered[-1][3] = True
        i = j + 1
    return terminal, rcode, ordered


def write_script(path, blocks, shebang, source):
    """Write blocks to a script, each preceded by a comment pointing to the chapter line."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(shebang + "\n")
        fh.write(f"# Extracted from {source} by {VERSION_NAME} v{VERSION} on {datetime.date.today()}\n\n")
        for lineno, code in blocks:
            fh.write(f"# ---- {source}, line {lineno}\n{code}\n\n")


def write_combined(path, ordered, source, data_dir):
    """
    Write one R script that runs all steps in chapter order.

    Terminal blocks are passed to bash via system2(); the script stops with the
    chapter line number when a step fails. A block that only changes directory
    becomes setwd(), so later steps run in that directory.
    """
    def map_data(code):
        # the CoCalc course data lives in ~/data/shared; point it at the local data folder
        for old in ("~/data/shared", "$HOME/data/shared", "${HOME}/data/shared"):
            code = code.replace(old, data_dir)
        return code

    ordered = [(k, l, map_data(c), e) for k, l, c, e in ordered]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("#!/usr/bin/env Rscript\n")
        fh.write(f"# Extracted from {source} by {VERSION_NAME} v{VERSION} on {datetime.date.today()}\n")
        fh.write("# Run from your test folder, e.g.: cd primer_test && Rscript <this file>\n")
        fh.write(f"# ~/data/shared is replaced by: {data_dir}\n\n")
        fh.write("# The folder you start in plays the role of the student's home directory (~ or $HOME on CoCalc).\n"
                 ".primer_home <- getwd()\n\n")
        fh.write(".primer_step <- function(line, code, expect_error = FALSE) {\n"
                 "  # run one Terminal block in bash; stop with the chapter line on failure\n"
                 "  message(\"\\n---- Terminal step, chapter line \", line)\n"
                 "  status <- system2(\"bash\", c(\"-c\", shQuote(code)))\n"
                 "  if (status != 0 && expect_error) {\n"
                 "    message(\"---- Expected error at chapter line \", line, \" (the book shows this error); continuing\")\n"
                 "  } else if (status != 0) {\n"
                 "    stop(\"Terminal step at chapter line \", line, \" failed (exit \", status, \")\", call. = FALSE)\n"
                 "  } else if (expect_error) {\n"
                 "    message(\"---- Note: the book expects an error at chapter line \", line, \", but the step succeeded\")\n"
                 "  }\n"
                 "}\n\n")
        for kind, lineno, code, expect_error in ordered:
            cd = re.fullmatch(r"\s*cd\s+(\S+)\s*", code)
            if kind == 'terminal' and cd:
                target = cd.group(1)
                # 'cd ~' / 'cd $HOME' -> the test folder; 'cd ~/x' / 'cd $HOME/x' -> test folder/x
                m_home = re.fullmatch(r"(~|\$HOME|\$\{HOME\})(/(.*))?", target)
                if m_home:
                    rest = m_home.group(3)
                    r_target = ".primer_home" if not rest else f'file.path(.primer_home, "{rest}")'
                else:
                    r_target = f'"{target}"'
                fh.write(f"# ---- {source}, line {lineno} (Terminal: cd {target})\n"
                         f"setwd({r_target})\n\n")
            elif kind == 'terminal':
                flag = ", expect_error = TRUE" if expect_error else ""
                note = " (expected error)" if expect_error else ""
                fh.write(f"# ---- {source}, line {lineno} (Terminal){note}\n"
                         f".primer_step({lineno}, r\"---[\n{code}\n]---\"{flag})\n\n")
            else:
                fh.write(f"# ---- {source}, line {lineno} (R)\n"
                         f"message(\"\\n---- R step, chapter line {lineno}\")\n{code}\n\n")


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

    terminal, rcode, ordered = extract(inp)
    if terminal:
        write_script(out_base + ".sh", terminal, "#!/usr/bin/env bash", os.path.basename(inp))
        logging.info("Wrote %d Terminal blocks to %s.sh", len(terminal), out_base)
    if rcode:
        write_script(out_base + ".R", rcode, "#!/usr/bin/env Rscript", os.path.basename(inp))
        logging.info("Wrote %d R blocks to %s.R", len(rcode), out_base)
    if args.combined and ordered:
        data_dir = os.path.abspath(os.path.expanduser(args.data_dir)) if args.data_dir \
            else os.path.join(in_dir, "data")
        if not os.path.isdir(data_dir):
            logging.warning("Data folder %s does not exist; ~/data/shared paths will not work", data_dir)
        write_combined(out_base + "_combined.R", ordered, os.path.basename(inp), data_dir)
        logging.info("~/data/shared replaced by %s", data_dir)
        logging.info("Wrote %d steps in chapter order to %s_combined.R", len(ordered), out_base)
    if not terminal and not rcode:
        logging.warning("No student code found in %s", inp)


if __name__ == "__main__":
    main()
