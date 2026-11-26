# Installing and testing the Quarto version (v3.0.0)

How to set up your Mac to build the book from the `quarto` branch and to check that the student exercises run. Run the commands in Terminal unless marked R.

## 1. Repository

The repository is `swvanderlaan/A_Practical_Primer_in_Human_Complex_Genetics` (renamed from `..._CoCalc`; both editions now live here). After renaming the repository on GitHub and the folder on your Mac:

```bash
cd ~/git/swvanderlaan/A_Practical_Primer_in_Human_Complex_Genetics
git remote set-url origin git@github.com:swvanderlaan/A_Practical_Primer_in_Human_Complex_Genetics.git
git remote -v          # check: origin points to the renamed repository

git switch quarto      # the Quarto version; master still holds the bookdown version
git status             # review the changes, then commit and push:
git add -A
git commit -m "v3.0.0 Move from bookdown to Quarto; fixes from 2026 course feedback"
git push -u origin quarto

# to update master afterwards
git switch master && git pull && git switch quarto
```

Note: GitHub forwards links to the old repository, but not the old website address (`swvanderlaan.github.io/A_Practical_Primer_in_Human_Complex_Genetics_CoCalc/`). If that link is used in course materials, create a small repository with the old name containing only an `index.html` that redirects to the new address.

## 2. Quarto

```bash
brew install --cask quarto
quarto --version       # 1.5 or newer
quarto check           # should find R, knitr and rmarkdown (after step 3)
```

## 3. R packages

R (in R or RStudio):

```r
install.packages(c("rmarkdown", "knitr", "flextable", "kableExtra", "formatR", "openxlsx",
                   "data.table", "tibble", "tidyverse", "dplyr", "plotly", "DT", "xml2",
                   "ggplot2", "ggpubr", "ggsci", "ggthemes", "qqman", "CMplot",
                   "remotes", "devtools", "usethis", "ieugwasr", "webshot", "webshot2", "tinytex"))
install.packages("BiocManager"); BiocManager::install("geneplotter", update = FALSE, ask = FALSE)
remotes::install_github("oliviasabik/RACER", upgrade = "never")
install.packages(c("TwoSampleMR", "MRInstruments"),
                 repos = c("https://mrcieu.r-universe.dev", "https://cloud.r-project.org"))
```

Run these lines one at a time: if a command asks a question (e.g. "Update all/some/none?"), the next pasted line is taken as the answer and silently not run. Check that everything is there:

```r
pkgs <- c("rmarkdown","knitr","flextable","kableExtra","data.table","tidyverse","ggpubr",
          "ggsci","ggthemes","qqman","CMplot","geneplotter","RACER","TwoSampleMR",
          "MRInstruments","ieugwasr","usethis","DT","plotly","openxlsx","formatR","webshot2")
setdiff(pkgs, rownames(installed.packages()))   # character(0) = all installed
```

`bookdown` is no longer needed.

### OpenGWAS token (for the Two-Sample MR chapter)

1. Log in at <https://api.opengwas.io/profile/> and generate a token.
2. In R: `usethis::edit_r_environ()`, add the line `OPENGWAS_JWT=<your token>`, save, restart R.
3. Check in R: `ieugwasr::get_opengwas_jwt()` (prints the token) and `ieugwasr::user()` (prints your user info).

### LDlink token (for the regional association plots)

1. Request a token at <https://ldlink.nih.gov/apiaccess>; it arrives by e-mail.
2. Add `LDLINK_TOKEN=<your token>` as a new line to `.Renviron` (`usethis::edit_r_environ()`), save, restart R.
3. Check in R: `nchar(Sys.getenv("LDLINK_TOKEN")) > 0` (TRUE).

Never commit `.Renviron`.

## 4. Command-line tools (for testing the exercises)

```bash
brew install plink1          # PLINK 1.9; installs the command `plink` (conflicts with `putty`, which also installs `plink`)
brew install plink2          # optional, for the PLINK 2 relatedness note (formula plink-ng; command `plink2`)
plink --version && plink2 --version
# EIGENSOFT (standalone edition only): no make/make install needed
git clone https://github.com/DReichLab/EIG.git ~/git/EIG
```

## 5. Build the book

The course data must be in `data/` (as on your Mac now; it is not in the repository).

```bash
quarto preview --profile cocalc          # live preview in the browser; re-renders on save
quarto render  --profile cocalc          # full build into _book/
quarto render  --profile standalone      # standalone edition
```

Check for broken figure, table or chapter references:

```bash
quarto render --profile cocalc 2>&1 | grep -E "WARN|ERROR"
```

No output means all references resolve. After a clean build, commit the `_freeze/` folder together with the chapters so the GitHub Action can build without R or the data.

## 6. Test the student exercises

The exercise code in the chapters is not run when the book is built (`eval = FALSE`); the book shows pre-made figures. To test what a student does, extract each chapter's code into one script that runs all Terminal and R steps in chapter order, and run it in a test folder **inside the repository**: `primer_test/` (ignored by git, so nothing ends up in a commit; delete it when you're done). The course data is read straight from the repository's `data/` folder: the script replaces the CoCalc path `~/data/shared` by it, so nothing is copied and nothing is added to your home folder.

```bash
cd ~/git/swvanderlaan/A_Practical_Primer_in_Human_Complex_Genetics
mkdir -p primer_test
for ch in 03_1_gwas_basics_cocalc 03_2_gwas_basics_sample_qc_cocalc 03_3_gwas_basics_snp_qc_cocalc \
          03_4_gwas_basics_association_testing_cocalc 03_5_gwas_basics_results_visualization_cocalc \
          03_6_gwas_basics_results_regional_plot_cocalc; do
  python3 scripts/extract_student_code.py --input $ch.qmd --output primer_test/$ch --combined --data-dir data
done
```

Then, in RStudio:

1. `setwd("~/git/swvanderlaan/A_Practical_Primer_in_Human_Complex_Genetics/primer_test")`. This folder plays the role of the student's home directory; the exercises create `dummy_project/` in it.
2. Check that RStudio finds PLINK: `Sys.which(c("plink", "plink2"))`. Empty? Add `PATH=/opt/homebrew/bin:${PATH}` to `.Renviron` and restart R.
3. Open `primer_test/03_1_gwas_basics_cocalc_combined.R` and use *Source with Echo* (or step through it with Cmd+Enter). Then 03_2, 03_3, ... 03_6, in order: each chapter builds on the files of the previous one. Start with a fresh session (*Session > Restart R*).
4. A run stops at the first failing step; the last `---- ... step, chapter line N` above the error tells you which part of the chapter to fix. Steps where the book itself shows an error (the 1000G merge in sample QC) are reported as "Expected error" and the run continues.

The extract script writes a date-prefixed log next to each chapter file (`*_extract_student_code.log`); these are ignored by git too.

**Clean up** when you're done: `rm -rf primer_test` (inside the repository).

If you followed an earlier version of these instructions, remove the old test folder and link from your home folder: `rm -rf ~/primer_test`, `rm ~/data/shared` (only removes the link), and `rmdir ~/data` (only removes the folder if it is empty).

## Checklist

- [X] Both profiles render without `WARN`/`ERROR`
- [X] Figures and tables show and are numbered; links in the text jump to them
- [X] Code blocks show Terminal / R / Output labels
- [X] Sample QC: heterozygosity plot code (ggplot version) runs; PCA orientation chunk flips the axes where needed; threshold catches the right samples
- [X] QC figures: threshold lines match the thresholds used in the PLINK commands
- [X] Relatedness: `plink2 --make-king-table` works
- [X] LocusZoom input file is tab-delimited
- [X] Two-Sample MR chapter runs with your token
- [X] Appendices (answers, licences, colophon) appear as A, B, C...
