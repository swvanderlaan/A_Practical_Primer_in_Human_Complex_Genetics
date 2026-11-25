# Installing and testing the Quarto version (v3.0.0)

How to set up your Mac to build the book from the `quarto` branch and to check that the student exercises run. Run the commands in Terminal unless marked R.

## 1. Repository

```bash
cd ~/git/swvanderlaan/A_Practical_Primer_in_Human_Complex_Genetics_CoCalc

# point origin at the CoCalc repo again; keep the new Standalone repo as a second remote
git remote set-url origin git@github.com:swvanderlaan/A_Practical_Primer_in_Human_Complex_Genetics_CoCalc.git
git remote add standalone git@github.com:swvanderlaan/A_Practical_Primer_in_Human_Complex_Genetics.git
git fetch --all --prune

git switch quarto      # the Quarto version; master still holds the bookdown version
git status             # review the staged renames and changes before committing
```

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
install.packages("BiocManager"); BiocManager::install("geneplotter")
remotes::install_github("oliviasabik/RACER")
install.packages(c("TwoSampleMR", "MRInstruments"),
                 repos = c("https://mrcieu.r-universe.dev", "https://cloud.r-project.org"))
```

`bookdown` is no longer needed.

### OpenGWAS token (for the Two-Sample MR chapter)

1. Log in at <https://api.opengwas.io/profile/> and generate a token.
2. In R: `usethis::edit_r_environ()`, add the line `OPENGWAS_JWT=<your token>`, save, restart R.
3. Check in R: `ieugwasr::get_opengwas_jwt()` (prints the token) and `ieugwasr::user()` (prints your user info).

Never commit `.Renviron`.

## 4. Command-line tools (for testing the exercises)

```bash
brew install plink           # PLINK 1.9
brew install plink2          # optional, for the PLINK 2 relatedness note
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

The exercise code in the chapters is not run when the book is built (`eval = FALSE`); the book shows pre-made figures. To test what a student does, extract a chapter's code into scripts and run them in a scratch folder with a copy of the raw data:

```bash
mkdir -p ~/primer_test && cd ~/primer_test
mkdir -p dummy_project
cp -R ~/git/swvanderlaan/A_Practical_Primer_in_Human_Complex_Genetics_CoCalc/data/{rawdata,ref_1kg_phase1_all,scripts,support} .

REPO=~/git/swvanderlaan/A_Practical_Primer_in_Human_Complex_Genetics_CoCalc
for ch in 03_1_gwas_basics_cocalc 03_2_gwas_basics_sample_qc_cocalc 03_3_gwas_basics_snp_qc_cocalc \
          03_4_gwas_basics_association_testing_cocalc 03_5_gwas_basics_results_visualization_cocalc \
          03_6_gwas_basics_results_regional_plot_cocalc; do
  python3 $REPO/scripts/extract_student_code.py --input $REPO/$ch.qmd --output ~/primer_test/$ch
done
```

Then work through each chapter in order: run the `.sh` file block by block in Terminal (or `bash -x <file>.sh` to run it in one go and see where it stops), and the `.R` file in RStudio with `~/primer_test` as working directory. Each block is preceded by a comment with the chapter line it came from, so a failure points straight to the text to fix.

The CoCalc chapters use `~/data/shared/...` paths; for a local test, create a link: `mkdir -p ~/data && ln -s ~/primer_test ~/data/shared`, or adjust the paths.

## Checklist

- [ ] Both profiles render without `WARN`/`ERROR`
- [ ] Figures and tables show and are numbered; links in the text jump to them
- [ ] Code blocks show Terminal / R / Output labels
- [ ] Sample QC: heterozygosity plot code (ggplot version) runs; PCA orientation chunk flips the axes where needed; threshold catches the right samples
- [ ] QC figures: threshold lines match the thresholds used in the PLINK commands
- [ ] Relatedness: `plink2 --make-king-table` works
- [ ] LocusZoom input file is tab-delimited
- [ ] Two-Sample MR chapter runs with your token
- [ ] Appendices (answers, licences, colophon) appear as A, B, C...
