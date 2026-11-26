# To do

Open items, roughly in order of priority (MoSCoW: **M**ust, **S**hould, **C**ould, **W**ould). Done items are listed in [CHANGELOG.md](CHANGELOG.md).

## Must
- [ ] Commit and push the `quarto` branch (with `_freeze/`); switch GitHub Pages to the Quarto version after merging into `master`.
- [ ] Regenerate the QC figures so the dashed threshold lines match the PLINK thresholds, and explain each line in the text.
- [ ] Update the "72" and "14 variants with 3+ alleles" counts in the sample QC Output blocks from a test run.
- [ ] Check the CoCalc data path: `~/data/shared` in the book versus `coursedata/genetic-epidemiology/shared` in the 2026 feedback.
- [ ] Lift over `rawdata` and `gwa` from hg18 to hg19 before the 1000G merge and the regional plots (UCSC `liftOver` or GWASLab); add a short liftOver chapter.
- [ ] Run `scripts/simulate_dummy_gwas.py` (written, tested on synthetic data) on the real 1000G reference; check the hits, QC issues and run time; then adapt the GWAS chapters to the new dataset (GRCh37, so no liftOver needed for it).
- [ ] Then compute LD locally with PLINK (`--r2 --ld-snp`) as an alternative to LDlink in the regional plots.
- [ ] Per-step output folders (`dummy_project/01_conversion`, `02_sample_qc`, ...); 3.4-3.6 (CoCalc) already use `dummy_project/gwas_results/`.
- [ ] Clean up the course data: inventory by name and size; keep course input and the files the book reads, delete intermediates; always keep the PCA `.eigenvec`/`.eigenval`; move `ref_hapmap3` (unused) to an archive; consider linking `data/` to Google Drive instead of a copy.
- [ ] Update the LocusZoom section to my.locuszoom.org (HapMap 2 / hg18 is no longer offered).
- [ ] Make the Standalone edition build without errors: its executed chunks read from `~/Desktop/practical`; read from `data/` instead (first four fixed in sample QC and association testing).
- [ ] Test the WTCCC1 (4.x) and post-GWAS (5.x) chapters with `extract_student_code.py --combined`.
- [ ] Conditional analysis and statistical fine-mapping (PLINK `--condition` or GCTA-COJO, then `susieR`).
- [ ] Colocalisation with formal testing (`coloc.abf`, `coloc.susie`, eQTL Catalogue).
- [ ] Partial recreation of the Cystatin C MR study.
- [ ] PDF and EPUB editions (`pdf:` and `epub:` formats in `_quarto.yml`; static images for interactive plots).

## Should
- [ ] Add GWASLab processing of a GWAS result.
- [ ] "Further resources" box: kinship/IBD table (AJHG 2014), plinkQC, `kgp` (1000G), GWASLab, long-range LD regions (b35-b38).
- [ ] Meta-analysis with the dummy data (METAL, stratified QQ plots; Standalone edition).
- [ ] Imputation chapter (Michigan/TOPMed server walkthrough with pre-imputation checks).
- [ ] New book cover (at least 1,400 px on the short side).
- [ ] Publish on Apple Books (free) and Zenodo (DOI per release): licence stays as is (all rights reserved, Dutch law), image rights, EPUB, company or private name (EU DSA), AI disclosure check. Use a Zenodo DOI instead of an ISBN.

## Could
- [ ] GWASToolKit and PlaqView/AtheroPortal lookups in a "further tools" box.
- [ ] Different font in the PDF.

## Dropped
- Full installation instructions for Ubuntu and Windows.
- MR-Base tutorial, replaced by Two-Sample MR.
