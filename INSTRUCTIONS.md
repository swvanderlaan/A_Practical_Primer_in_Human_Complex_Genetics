# Maintainer instructions

Notes for building, testing and publishing the book. For a first set-up and a full test of the exercises, see [TESTING.md](TESTING.md); open items are in [TODO.md](TODO.md), changes per version in [CHANGELOG.md](CHANGELOG.md).

## Building the book

From version 3.0.0 the book is built with [Quarto](https://quarto.org/docs/books/) instead of `bookdown`. The `quarto` branch holds this version; `master` still holds the `bookdown` version that is currently online.

There are two editions, built from the same chapters with Quarto _profiles_:

| Profile      | Edition                                   | Chapters listed in        |
|--------------|-------------------------------------------|---------------------------|
| `cocalc`     | CoCalc course version (default)           | `_quarto-cocalc.yml`      |
| `standalone` | Own laptop or server                      | `_quarto-standalone.yml`  |

```bash
# preview while writing (re-renders on save)
quarto preview --profile cocalc

# full build into _book/
quarto render --profile cocalc
quarto render --profile standalone
```

Requirements: [Quarto](https://quarto.org/docs/get-started/) (>= 1.5), `R` with the packages in `scripts/packages.R`, and the course data in `data/` (not in the repository).

**Freezing.** Code results are cached in `_freeze/` (`execute: freeze: auto`). A chapter is only re-executed when its source changes. Commit `_freeze/` together with the chapter, so that the GitHub Action can build the book without `R` or the data. Note: a change in an included file (such as `_opengwas-token.qmd`, included in both Getting started chapters) does not trigger a re-run; delete that chapter's folder in `_freeze/` (e.g. `rm -rf _freeze/02_4_gettingstarted_cocalc`) and render again.

**Code blocks.** Code to run in the Terminal is labelled _Terminal_, code to run in `R`/RStudio is labelled _R_, and program output is labelled _Output_.

**Publishing.** `.github/workflows/quarto-book.yml` renders the CoCalc edition on every push to `quarto` or `master` (and uploads the HTML as a build artifact); only a push to `master` publishes it to the `gh-pages` branch, which GitHub Pages serves. Before pushing, render locally and commit `_freeze/`.

## Data

The course data lives on Google Drive and is not in git (`/data/*` is ignored, except `data/scripts/`, `data/support/` and the readmes). The WTCCC1 data is restricted and must never be shared or committed.

**Link the data into the repository** (once, and again if the Drive folders move). The book and the exercise tests then find everything under `data/`, without a copy:

```bash
git checkout -- data/                         # restore the small tracked files (scripts/, support/, readmes)
git rm -r --cached --quiet data/dummy_project # stop tracking these; data/dummy_project becomes a link
rm -rf data/dummy_project                     # remove the restored folder, so the link can be made
scripts/link_data.sh \
  -d "$HOME/Library/CloudStorage/GoogleDrive-s.w.vanderlaan@gmail.com/My Drive/Genomics/Lectures/A_primer_in_Human_Cardiovascular_Genetics_data" \
  -w "$HOME/Library/CloudStorage/GoogleDrive-s.w.vanderlaan@gmail.com/My Drive/Genomics/Lectures/A_primer_in_Human_Cardiovascular_Genetics_data_wtccc1"
ls -l data/
```

`link_data.sh` accepts both layouts: `course_input/` + `reference_results/dummy_project`, or all folders directly under the data folder.

## A new dummy GWAS dataset

`scripts/simulate_dummy_gwas.py` creates a shareable, genome-wide case-control dataset (default 500 cases, 1,500 controls, 2,000,000 SNPs on chromosomes 1-22, X and XY, plus all usable Y and MT SNPs) from the 1000G phase 1 reference (GRCh37). Every simulated person is a mosaic of genome segments of real European reference samples, so LD is realistic; five causal SNPs on different autosomes (never HLA, the chr8 inversion or chr17q21) give genome-wide hits; and QC issues are planted (sex mismatches, duplicates, relatives, non-European samples, missingness, HWE), plus spurious associations that are genome-wide significant before QC and removed by it: differential missingness (`--geno`, `--test-missing`), a genotyping batch error in controls (`--hwe` in controls) and rare variants carried almost only by cases (`--maf 0.01`). The causal SNPs and all planted issues are listed in `<out>.truth.txt`.

```bash
python3 scripts/simulate_dummy_gwas.py \
  --input data/ref_1kg_phase1_all/1kg_phase1_all \
  --output ~/tmp/dummy_gwas/dummy_gwas --seed 2026
```

Only `numpy` is needed. Use `--help` for all options (number of cases/controls/SNPs/hits, `--no-qc-issues`, `--hits` to choose the causal SNPs). The first run reads the 12 GB reference; on Google Drive that means downloading it once.
