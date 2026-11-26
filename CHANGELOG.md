# Changelog

All notable changes to _A Practical Primer in Human Complex Genetics_, newest first.

* v3.0.0 (2026-11-26) Moved from `bookdown` to Quarto: one source, two profiles (CoCalc and Standalone); repository renamed from `..._CoCalc`. Fixed broken figure, table and chapter cross-references. Code blocks labelled Terminal, R or Output. OpenGWAS and LDlink token set-up in Getting started; Two-Sample MR and RACER calls updated to the current packages. Sample QC: heterozygosity plot code, PC orientation before the PCA threshold, PLINK 2 relatedness (`--make-king-table`), SNP ID lists, exclusion of SNPs on a different chromosome before the 1000G merge (hg18 vs hg19), explanation of het. haploid warnings. SNP QC: explanation of ALL/AFF/UNAFF. Association testing onwards: results in `dummy_project/gwas_results/` instead of deleting earlier work; answer to "load the data" shown in a collapsible box. Fixed paths (`data/`, `COURSE_loc`, hard-coded user paths), `ggplot2::last_plot()`/`ggplot2::ggsave()` with fixed plot sizes, WTCCC1 SNP call-rate plot overwriting the HWE plot, re-runnable steps (`mkdir -p`, `gzip -f`), tab-delimited LocusZoom input, no `make` for EIGENSOFT, PLINK installation via Homebrew/conda, appendices, typo fixes. Added `scripts/extract_student_code.py` and TESTING.md to test the exercises end to end. Addresses the feedback of the 2026 course.
* v2.2.5 Name change in preparation of the Standalone version.
* v2.2.4 Version fix on the main page. Fixed error on display of questions for TwoSample MR in Answer-chapter. Fixed command in WTCCC1 association chapter.
* v2.2.4 Removed code block in FUMA-chapter. Added quick-and-dirty fix for MRBase. Added Answers to questions.
* v2.2.3 Fixes to the rendering of the book. Fixes to the references. Fixed issue with FUMA input file. Splitted the WTCCC1 analyses in 3 parts, first introduction, then quality control, finally association testing.
* v2.2.2 Small fix to remove `knitr` codes. Fixed errors in `opts$chunks` for `knitr` and `rmarkdown` regarding 'echo'.
* v2.2.1 Small fixes to references. Added book cover. Added favicon and Apple-touch-icon.
* v2.2.0 Created a full CoCalc version, and a separate Standalone version.
* v2.1.2 Small fix to directory reference.
* v2.1.1 Finalized CoCalc instructions. Added Team chapter. Fixed issue with Two-Sample MR. Fixed issue with regional association plotting. Checked Questions and Answers. Edited the To-Do list
* v2.1.0 Added CoCalc instructions. Added Standalone instructions. Added chapter on used-programs. Re-organized 'Getting Started' chapter. Updated To-Do list in readme.
* v2.0.6 Fixes to the visualization chapter where data was not properly loaded. Fix to the references in the WTCCC1 chapter where they were not properly generated.
* v2.0.5 Added all header-images. Fixed references to tables and figures.
* v2.0.4 Added WTCCC1 introduction; added WTCCC1 analyses and visualization. Add post-GWAs chapter.
* v2.0.3 Added GWAS visualization.
* v2.0.2 Added GWAS testing. Updates to saving of plots. Re-organization of data.
* v2.0.1 Fixed standalone instructions. Fixed dummy GWAS project.
* v1.0.0 Initial version.
