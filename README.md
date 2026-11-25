# A Practical Primer in Human Complex Genetics

_A Practical Primer in Human Complex Genetics_ was originally written for the **Genetic Epidemiology** course organized by the [Master Epidemiology](https://epidemiology-education.nl) of Utrecht University, but can be used as a practical guide and companion to learning and doing a genome-wide association study (GWAS).

It is available as an online book at [swvanderlaan.github.io/A_Practical_Primer_in_Human_Complex_Genetics_CoCalc](https://swvanderlaan.github.io/A_Practical_Primer_in_Human_Complex_Genetics_CoCalc/). A PDF and EPUB version is forthcoming.

This book was made possible by the kind help of Caspar J. van Lissa who wrote an excellent instruction through an example GitBook https://cjvanlissa.github.io/gitbook-demo/.

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

**Freezing.** Code results are cached in `_freeze/` (`execute: freeze: auto`). A chapter is only re-executed when its source changes. Commit `_freeze/` together with the chapter, so that the GitHub Action can build the book without `R` or the data.

**Code blocks.** Code to run in the Terminal is labelled _Terminal_, code to run in `R`/RStudio is labelled _R_, and program output is labelled _Output_.

**Publishing.** `.github/workflows/quarto-book.yml` renders the book on every push to `quarto` and uploads the HTML as a build artifact. Publishing to GitHub Pages is switched off until the Quarto version replaces the `bookdown` version; see the comments in the workflow.

#### Changes log
    
    _Version:_      v3.0.0</br>
    _Last update:_  2026-11-24</br>
    _Written by:_   Sander W. van der Laan (s.w.vanderlaan-2[at]umcutrecht.nl).
    
    **MoSCoW To-Do List**
    The things we Must, Should, Could, and Would have given the time we have.
    _M_
    
    - [x] `M` create a separate CoCalc version
    ~- [] `M` add in full installation instructions for UBUNTU > DROPPED~
    - [x] `M` add in full installation instructions for macOS
    - [x] `M` create chapter on CoCalc
    - [x] `M` redesign 'Getting Started' chapter
    - [x] `M` add proper team-page
    - [x] `M` fix regional association plotting
    - [x] `M` fix issue with api of Two Sample MR > run the codes.
    - [x] `M` fix issue with `api of Two Sample MR`cat: /Users/USERNAME/Desktop/practical/gwas/data.assoc.logistic.clumped: No such file or     directory` - this was not run yet
    - [x] `M` fix images per header in GitBook (not showing)
    - [] `M` conditional analysis
    - [] `M` statistical finemapping
    - [] `M` colocalization with formal testing
    - [x] `M` MRbase tutorial > dropped in favor of Two Sample MR > added a quick-and-dirty fix for now
    - [] `M` Add partial recreation of the Cystatin C MR study
    - [x] `M` overall rendering too slow, paste in images as figure instead of on the fly generating
    - [] `M` fix issue with PDF creation
    - [] `M` fix issue with EPUB creation
    - [] `M` fix issue with EPUB creation and images
    - [] `M` get ISBN number
    - [x] `M` Upgrade to Quarto https://quarto.org/docs/books/ (v3.0.0, `quarto` branch)
    - [] `M` regenerate QC figures so the threshold lines match the thresholds applied in PLINK
    - [] `M` re-render all figures with the corrected code and commit `_freeze/`
    - [] `M` update the LocusZoom section to my.locuszoom.org (hg18/HapMap 2 is no longer available)
    - [] `S` give each step its own output folder to make it easier to keep track of files
     
    _S_
    - [] `S` meta-analysis with dummy data
        - `S` HPC version with MetaGWASToolKit
        - `S` including stratified QQ plots
        - `S` stand-alone version with METAL
    - [] `S` add online imputation chapter
        - [] `S` fix images per header in EPUB
    - [] `S` PDF is not formatted properly (text runs over)
    - [] `S` EPUB is not formatted properly (text runs over)
    - [] `S` different setup for the chapter Additional chapters (this as a Apendix)
    - [x] `S` fix the way the team is displayed
    - [] `S` fix book cover > version 2024 'quick and dirty'
      - https://www.designhill.com/design-blog/the-perfect-ebook-cover-size-guide-and-publishing-tips/
      - https://snappa.com/blog/ebook-cover-size/
      - https://kdp.amazon.com/en_US/help/topic/G200645690.
    - [] `S` add in chapter on liftOver
    
    _C_
    - [] `C` GWASToolKit
    - [] `C` PlaqView lookups
    - [] `C` Different font type in PDF
    
    _W_
    ~- [] `W` add in full installation instructions for Windows > DROPPED~
    - [x] `W` add favicon and Apple-touch-icon
      - https://iconifier.net

    **Changes log**
    * v3.0.0 Moved from `bookdown` to Quarto (one source, two profiles: CoCalc and Standalone). Fixed broken figure, table and chapter cross-references. Code blocks are now labelled Terminal, R or Output. Two-Sample MR: added OpenGWAS token (JWT) set-up, required since May 2024. Fixed heterozygosity plot code, added PC sign orientation before the PCA threshold, PLINK 2 relatedness (`--make-king-table`), explanation of ALL/AFF/UNAFF in the HWE output, tab-delimited LocusZoom input, removed hard-coded paths, removed unnecessary `make` for EIGENSOFT, added PLINK installation via Homebrew/conda, typo fixes. Addresses the feedback of the 2026 course.
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

--------------
------
<sup>Copyright 1979-2026. All rights reserved. Sander W. van der Laan | s.w.vanderlaan [at] gmail.com | [vanderlaanand.science](https://vanderlaanand.science). Published with [Quarto](https://quarto.org).</sup>
