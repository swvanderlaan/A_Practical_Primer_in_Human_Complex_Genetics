#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simulate_dummy_gwas.py

Create a shareable, genome-wide dummy case-control GWAS dataset with realistic
linkage disequilibrium (LD), for 'A Practical Primer in Human Complex Genetics'.

How it works
------------
1. Reference: a PLINK binary fileset of 1000 Genomes phase 1 (GRCh37/hg19), plus
   its .pheno file with the columns Family_ID, Individual_ID, Gender, Phenotype,
   Population (the file used in the sample QC chapter).
2. Variants: an array-like, genome-wide set of biallelic SNPs is drawn from the
   reference (default 500,000 on chromosomes 1-22 and X, plus all usable Y, XY
   and MT SNPs), keeping SNPs with a minor allele frequency (MAF) >= --maf in the
   European (EUR) reference samples.
3. Individuals: every simulated person is a mosaic of genome segments copied from
   real EUR reference samples (segment lengths ~ exponential, mean --segment-mb).
   Within a segment the genotypes are those of a real person, so LD between
   nearby SNPs is real European LD. Chromosome X is copied from donors of the
   same sex; Y (males only) and MT are copied whole from one donor.
4. Phenotype: --n-hits causal SNPs on different autosomes (never in the HLA
   region, the chr8 inversion or chr17q21) get an effect on disease risk in a
   logistic model with prevalence --prevalence, age and sex. Individuals are
   generated until --n-cases cases and --n-controls controls are collected; the
   effect sizes are tuned until every causal SNP reaches P < --target-p in a
   simple allelic test, so the book has clear genome-wide hits.
5. QC issues (unless --no-qc-issues): sex mismatches, duplicates, first-degree
   relatives, samples of non-European ancestry, samples and SNPs with high
   missingness, and SNPs out of Hardy-Weinberg equilibrium, so the QC chapters
   have something to find.
6. Spurious associations (unless --no-qc-issues): SNPs that are genome-wide
   significant before QC only because of an artefact, each removed by a standard
   QC step: differential missingness between cases and controls (--geno,
   --test-missing), a genotyping batch error in controls (--hwe in controls), and
   rare variants carried almost only by cases (--maf 0.01).

Output (all with the same basename)
-----------------------------------
  <out>.bed/.bim/.fam   PLINK binary fileset (phenotype: 1 = control, 2 = case)
  <out>.covar           FID, IID, AGE, SEX
  <out>.truth.txt       the causal SNPs (with effect sizes) and all planted QC issues
  <out>.log             log file
By default <out> is <input dir>/<YYYYMMDD>_<input name>_annotated; use --output to
choose another place and name (recommended, e.g. --output ~/tmp/dummy_gwas).

Only numpy is required. The reference .bed is read with memory mapping; on a
cloud drive the first run downloads the file.

Usage
-----
  python3 scripts/simulate_dummy_gwas.py --input <path>/ref_1kg_phase1_all/1kg_phase1_all \\
      --output <path>/dummy_gwas --seed 2026

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

VERSION_NAME = "simulate_dummy_gwas"
VERSION = "1.2.0"
VERSION_DATE = "2026-11-26"

import argparse
import datetime
import logging
import math
import os
import sys

import numpy as np

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------
# PLINK chromosome codes: 23 = X, 24 = Y, 25 = XY (pseudo-autosomal), 26 = MT
CHR_CODES = {str(i): i for i in range(1, 27)}
CHR_CODES.update({"X": 23, "Y": 24, "XY": 25, "MT": 26, "M": 26, "chrX": 23, "chrY": 24, "chrM": 26})
CHR_ORDER = list(range(1, 27))
AUTOSOMES = set(range(1, 23))

# super-populations of the 1000G phase 1 populations
SUPERPOP = {"CEU": "EUR", "FIN": "EUR", "GBR": "EUR", "IBS": "EUR", "TSI": "EUR",
            "YRI": "AFR", "LWK": "AFR", "ASW": "AFR",
            "CHB": "ASN", "CHS": "ASN", "JPT": "ASN",
            "MXL": "AMR", "CLM": "AMR", "PUR": "AMR"}

# regions (GRCh37) where no causal SNP is placed: HLA/MHC, chr8p23 inversion, chr17q21
EXCLUDED_FOR_HITS = [(6, 25_000_000, 35_000_000), (8, 7_000_000, 13_000_000), (17, 40_000_000, 46_000_000)]

# PLINK .bed 2-bit codes -> number of A1 alleles (-1 = missing)
DECODE = np.array([2, -1, 1, 0], dtype=np.int8)
BED_MAGIC = bytes([0x6C, 0x1B, 0x01])


# ---------------------------------------------------------------------------
# command line and logging
# ---------------------------------------------------------------------------
def parse_args():
    """Parse the command-line arguments."""
    p = argparse.ArgumentParser(
        prog=VERSION_NAME,
        description=f"{VERSION_NAME} v{VERSION} ({VERSION_DATE}): simulate a genome-wide dummy "
                    "case-control GWAS dataset with realistic LD from 1000 Genomes EUR.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--input", required=True,
                   help="PLINK prefix of the 1000G phase 1 reference (without .bed/.bim/.fam).")
    p.add_argument("--pheno", default=None,
                   help="Reference population file (default: <input>.pheno).")
    p.add_argument("--output", default=None,
                   help="Output prefix (default: <input dir>/<date>_<input name>_annotated).")
    p.add_argument("--n-cases", type=int, default=500, help="Number of cases.")
    p.add_argument("--n-controls", type=int, default=1500, help="Number of controls.")
    p.add_argument("--n-snps", type=int, default=2_000_000,
                   help="Number of SNPs on chromosomes 1-22, X and XY (all usable Y and MT SNPs come on top).")
    p.add_argument("--maf", type=float, default=0.01, help="Minimum MAF in EUR for chromosomes 1-22 and X.")
    p.add_argument("--n-hits", type=int, default=5, help="Number of causal SNPs, each on its own autosome.")
    p.add_argument("--hits", default=None,
                   help="Optional comma-separated rsIDs to use as causal SNPs instead of a random choice.")
    p.add_argument("--target-p", type=float, default=1e-10,
                   help="Effect sizes are increased until every causal SNP has P below this value.")
    p.add_argument("--prevalence", type=float, default=0.10, help="Disease prevalence in the population.")
    p.add_argument("--segment-mb", type=float, default=4.0,
                   help="Mean length (Mb) of the genome segments copied from one donor.")
    p.add_argument("--n-spurious", type=int, default=4,
                   help="Number of spurious associations per artefact type (3 types).")
    p.add_argument("--no-qc-issues", action="store_true",
                   help="Do not plant QC issues (sex mismatches, relatives, outliers, missingness, HWE).")
    p.add_argument("--seed", type=int, default=2026, help="Random seed (same seed = same dataset).")
    p.add_argument("--version", action="version", version=f"{VERSION_NAME} v{VERSION} ({VERSION_DATE})")
    return p.parse_args()


def setup_logging(log_path):
    """Log to file and to the console."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.FileHandler(log_path, mode="w"), logging.StreamHandler(sys.stdout)])


# ---------------------------------------------------------------------------
# reading the reference
# ---------------------------------------------------------------------------
def read_fam(path):
    """Read a .fam file; returns lists of FID, IID and sex (1 = male, 2 = female, 0 = unknown)."""
    fid, iid, sex = [], [], []
    with open(path) as fh:
        for line in fh:
            f = line.split()
            if len(f) < 6:
                continue
            fid.append(f[0]); iid.append(f[1]); sex.append(int(f[4]) if f[4] in ("1", "2") else 0)
    return fid, iid, np.array(sex, dtype=np.int8)


def read_populations(path):
    """Read the reference population file (whitespace-separated, with a header containing
    Individual_ID and Population); returns a dict IID -> population."""
    pops = {}
    with open(path) as fh:
        header = fh.readline().split()
        try:
            i_id, i_pop = header.index("Individual_ID"), header.index("Population")
        except ValueError:
            sys.exit(f"ERROR: {path} needs the columns Individual_ID and Population")
        for line in fh:
            f = line.split()
            if len(f) > max(i_id, i_pop):
                pops[f[i_id]] = f[i_pop]
    return pops


def is_snp(a1, a2):
    """True for a biallelic SNP with single-base alleles A/C/G/T."""
    return len(a1) == 1 and len(a2) == 1 and a1 in "ACGT" and a2 in "ACGT" and a1 != a2


def count_bim(path):
    """First pass over the .bim: count usable SNPs per chromosome."""
    counts = {c: 0 for c in CHR_ORDER}
    with open(path) as fh:
        for line in fh:
            f = line.split()
            c = CHR_CODES.get(f[0])
            if c and is_snp(f[4], f[5]):
                counts[c] += 1
    return counts


def select_bim(path, keep_prob, rng):
    """Second pass over the .bim: keep usable SNPs with a per-chromosome probability.
    Returns a dict of arrays (row index in the .bed, chr, id, cm, bp, a1, a2)."""
    rows, chrs, ids, cms, bps, a1s, a2s = [], [], [], [], [], [], []
    seen_ids, seen_pos = set(), set()
    with open(path) as fh:
        for row, line in enumerate(fh):
            f = line.split()
            c = CHR_CODES.get(f[0])
            if not c or not is_snp(f[4], f[5]):
                continue
            if rng.random() >= keep_prob[c]:
                continue
            bp = int(f[3])
            if f[1] in seen_ids or (c, bp) in seen_pos or f[1] == ".":
                continue  # no duplicate IDs or positions in the dummy data
            seen_ids.add(f[1]); seen_pos.add((c, bp))
            rows.append(row); chrs.append(c); ids.append(f[1]); cms.append(f[2])
            bps.append(bp); a1s.append(f[4]); a2s.append(f[5])
    return {"row": np.array(rows, dtype=np.int64), "chr": np.array(chrs, dtype=np.int16),
            "id": np.array(ids, dtype=object), "cm": np.array(cms, dtype=object),
            "bp": np.array(bps, dtype=np.int64), "a1": np.array(a1s, dtype=object),
            "a2": np.array(a2s, dtype=object)}


class BedReader:
    """Read genotypes of selected SNPs (rows) and samples (columns) from a SNP-major PLINK .bed."""

    def __init__(self, path, n_samples):
        self.n = n_samples
        self.nbytes = (n_samples + 3) // 4
        with open(path, "rb") as fh:
            if fh.read(3) != BED_MAGIC:
                sys.exit(f"ERROR: {path} is not a SNP-major PLINK .bed file")
        self.mm = np.memmap(path, dtype=np.uint8, mode="r", offset=3)

    def read(self, rows, cols=None, chunk=20_000):
        """Return an int8 matrix (len(rows) x len(cols)) with the number of A1 alleles (-1 = missing)."""
        rows = np.asarray(rows, dtype=np.int64)
        ncol = self.n if cols is None else len(cols)
        out = np.empty((len(rows), ncol), dtype=np.int8)
        shifts = np.array([0, 2, 4, 6], dtype=np.uint8)
        for s in range(0, len(rows), chunk):
            r = rows[s:s + chunk]
            idx = (r[:, None] * self.nbytes + np.arange(self.nbytes)[None, :])
            raw = self.mm[idx]                                   # (k, nbytes)
            codes = (raw[:, :, None] >> shifts) & 3              # (k, nbytes, 4)
            g = DECODE[codes.reshape(len(r), -1)[:, :self.n]]
            out[s:s + chunk] = g if cols is None else g[:, cols]
        return out


def eur_maf(geno):
    """Minor allele frequency per SNP (rows) ignoring missing values."""
    valid = geno >= 0
    n = valid.sum(axis=1)
    a1 = np.where(valid, geno, 0).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        f = np.where(n > 0, a1 / (2.0 * n), 0.0)
    return np.minimum(f, 1.0 - f)


# ---------------------------------------------------------------------------
# simulation helpers
# ---------------------------------------------------------------------------
def segment_plan(bp, mean_len, rng):
    """Split a chromosome (SNP positions bp, sorted) into segments with exponential lengths.
    Returns the start indices (into bp) of the segments; the first is always 0."""
    lo, hi = bp[0], bp[-1]
    breaks, pos = [], lo
    while True:
        pos += rng.exponential(mean_len)
        if pos >= hi:
            break
        breaks.append(pos)
    starts = np.searchsorted(bp, np.array(breaks, dtype=float)) if breaks else np.array([], dtype=np.int64)
    return np.unique(np.concatenate([[0], starts]))


def allelic_p(g_case, g_ctrl):
    """P-value of a 1-df allelic chi-square test (2 x 2 table of allele counts)."""
    a = g_case.sum(); b = 2 * len(g_case) - a
    c = g_ctrl.sum(); d = 2 * len(g_ctrl) - c
    n = a + b + c + d
    den = (a + b) * (c + d) * (a + c) * (b + d)
    if den == 0:
        return 1.0
    chi2 = n * (a * d - b * c) ** 2 / den
    return math.erfc(math.sqrt(chi2 / 2.0))


def allelic_p_status(g, status):
    """Allelic test P for one SNP (A1 counts, -1 missing) given status (2 = case, 1 = control)."""
    ok = g >= 0
    return allelic_p(g[ok & (status == 2)], g[ok & (status == 1)])


def logistic(x):
    """Numerically stable logistic function."""
    return 1.0 / (1.0 + np.exp(-x))


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------
def encode_bed(geno):
    """Encode an int8 matrix (SNPs x samples, A1 counts, -1 missing) to SNP-major .bed bytes."""
    code = np.empty(geno.shape, dtype=np.uint8)
    code[geno == 2] = 0
    code[geno == 1] = 2
    code[geno == 0] = 3
    code[geno < 0] = 1
    n = geno.shape[1]
    pad = (-n) % 4
    if pad:
        code = np.concatenate([code, np.zeros((geno.shape[0], pad), dtype=np.uint8)], axis=1)
    code = code.reshape(geno.shape[0], -1, 4)
    packed = code[:, :, 0] | (code[:, :, 1] << 2) | (code[:, :, 2] << 4) | (code[:, :, 3] << 6)
    return packed.astype(np.uint8).tobytes()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    args = parse_args()
    ref = os.path.abspath(os.path.expanduser(args.input))
    for ext in (".bed", ".bim", ".fam"):
        if not os.path.isfile(ref + ext):
            sys.exit(f"ERROR: {ref + ext} not found")
    pheno = os.path.expanduser(args.pheno) if args.pheno else ref + ".pheno"
    if not os.path.isfile(pheno):
        sys.exit(f"ERROR: population file {pheno} not found (use --pheno)")
    today = datetime.date.today().strftime("%Y%m%d")
    out = os.path.abspath(os.path.expanduser(args.output)) if args.output else \
        os.path.join(os.path.dirname(ref), f"{today}_{os.path.basename(ref)}_annotated")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    log_path = os.path.join(os.path.dirname(out), f"{today}_{os.path.basename(out)}.log")
    setup_logging(log_path)
    log = logging.getLogger()
    log.info("%s v%s (%s)", VERSION_NAME, VERSION, VERSION_DATE)
    log.info("Reference: %s | output: %s | seed: %d", ref, out, args.seed)
    rng = np.random.default_rng(args.seed)
    seg_len = args.segment_mb * 1e6

    # --- samples and populations ---------------------------------------------------------
    _, ref_iid, ref_sex = read_fam(ref + ".fam")
    pops = read_populations(pheno)
    superpop = np.array([SUPERPOP.get(pops.get(i, ""), "NA") for i in ref_iid])
    eur = np.where(superpop == "EUR")[0]
    eur_m, eur_f = eur[ref_sex[eur] == 1], eur[ref_sex[eur] == 2]
    afr, asn = np.where(superpop == "AFR")[0], np.where(superpop == "ASN")[0]
    log.info("Reference samples: %d (EUR %d: %d male, %d female; AFR %d; ASN %d)",
             len(ref_iid), len(eur), len(eur_m), len(eur_f), len(afr), len(asn))
    if len(eur_m) < 10 or len(eur_f) < 10:
        sys.exit("ERROR: too few EUR samples of each sex in the reference")
    bed = BedReader(ref + ".bed", len(ref_iid))

    # --- variant selection -------------------------------------------------------------
    log.info("Counting usable SNPs in %s.bim (this takes a while for 1000G) ...", ref)
    counts = count_bim(ref + ".bim")
    main_chr = [c for c in CHR_ORDER if c in AUTOSOMES or c in (23, 25)]
    n_main = sum(counts[c] for c in main_chr)
    if n_main == 0:
        sys.exit("ERROR: no usable SNPs on chromosomes 1-22/X")
    log.info("Usable SNPs per chromosome: %s", ", ".join(f"{c}:{counts[c]}" for c in CHR_ORDER if counts[c]))
    # Most 1000G SNPs are rare. Round 1 assumes ~25% of SNPs pass the MAF filter; if fewer pass,
    # round 2 selects a larger random set, sized with the pass rate measured in round 1.
    pass_rate = 0.25
    for rnd in (1, 2):
        frac = min(1.0, 1.2 * args.n_snps / (n_main * pass_rate))
        keep_prob = {c: (frac if c in main_chr else 1.0) for c in CHR_ORDER}
        snps = select_bim(ref + ".bim", keep_prob, rng)
        log.info("Round %d: %d candidate SNPs (%.1f%% of chromosomes 1-22/X/XY)", rnd, len(snps["row"]), 100 * frac)
        keep = np.zeros(len(snps["row"]), dtype=bool)
        maf = np.zeros(len(snps["row"]))
        for s in range(0, len(snps["row"]), 50_000):
            g = bed.read(snps["row"][s:s + 50_000], eur)
            m = eur_maf(g)
            maf[s:s + 50_000] = m
            main = np.isin(snps["chr"][s:s + 50_000], main_chr)
            keep[s:s + 50_000] = np.where(main, m >= args.maf, m > 0)
        is_main = np.isin(snps["chr"], main_chr)
        n_pass = int((keep & is_main).sum())
        log.info("Round %d: %d SNPs on chromosomes 1-22/X/XY pass MAF >= %g", rnd, n_pass, args.maf)
        if n_pass >= args.n_snps or frac >= 1.0:
            break
        pass_rate = max(n_pass / max(1, int(is_main.sum())), 1e-3)
    snps = {k: v[keep] for k, v in snps.items()}
    maf = maf[keep]
    # down-sample chromosomes 1-22/X to --n-snps
    main_idx = np.where(np.isin(snps["chr"], main_chr))[0]
    if len(main_idx) > args.n_snps:
        drop = rng.choice(main_idx, len(main_idx) - args.n_snps, replace=False)
        mask = np.ones(len(snps["row"]), dtype=bool); mask[drop] = False
        snps = {k: v[mask] for k, v in snps.items()}; maf = maf[mask]
    order = np.lexsort((snps["bp"], snps["chr"]))
    snps = {k: v[order] for k, v in snps.items()}; maf = maf[order]
    per_chr = {c: int((snps["chr"] == c).sum()) for c in CHR_ORDER}
    log.info("Final SNPs: %d (%s)", len(snps["row"]),
             ", ".join(f"{c}:{n}" for c, n in per_chr.items() if n))
    if len(main_idx) < args.n_snps:
        log.warning("Only %d SNPs on 1-22/X/XY pass the MAF filter (asked %d)", len(main_idx), args.n_snps)

    # --- causal SNPs -------------------------------------------------------------------
    if args.hits:
        wanted = [h.strip() for h in args.hits.split(",") if h.strip()]
        hit_idx = []
        for h in wanted:
            w = np.where(snps["id"] == h)[0]
            if len(w) == 0:
                sys.exit(f"ERROR: causal SNP {h} is not among the selected SNPs")
            hit_idx.append(int(w[0]))
    else:
        ok = np.isin(snps["chr"], list(AUTOSOMES)) & (maf >= 0.20)
        for c, lo, hi in EXCLUDED_FOR_HITS:
            ok &= ~((snps["chr"] == c) & (snps["bp"] >= lo) & (snps["bp"] <= hi))
        for c in AUTOSOMES:  # keep 5 Mb away from chromosome ends, so regional plots have room
            on = snps["chr"] == c
            if on.any():
                lo, hi = snps["bp"][on].min(), snps["bp"][on].max()
                ok &= ~(on & ((snps["bp"] < lo + 5e6) | (snps["bp"] > hi - 5e6)))
        cand_chr = sorted({int(c) for c in snps["chr"][ok]})
        if len(cand_chr) < args.n_hits:
            sys.exit(f"ERROR: only {len(cand_chr)} autosomes have suitable causal SNPs")
        hit_chr = rng.choice(cand_chr, args.n_hits, replace=False)
        hit_idx = [int(rng.choice(np.where(ok & (snps["chr"] == c))[0])) for c in hit_chr]
    if len({int(snps["chr"][i]) for i in hit_idx}) < len(hit_idx):
        sys.exit("ERROR: causal SNPs must be on different chromosomes")
    hit_idx = sorted(hit_idx, key=lambda i: (snps["chr"][i], snps["bp"][i]))
    hit_geno = bed.read(snps["row"][hit_idx], eur)          # (n_hits x n_eur) donor genotypes
    hit_freq = np.array([np.mean(np.where(g >= 0, g, 0)) / 2 for g in hit_geno])
    for i, f in zip(hit_idx, hit_freq):
        log.info("Causal SNP %s chr%d:%d (A1 %s, EUR A1 frequency %.3f)",
                 snps["id"][i], snps["chr"][i], snps["bp"][i], snps["a1"][i], f)

    # --- phenotype: sample individuals until the case/control quota is filled ---------
    n_target = args.n_cases + args.n_controls
    beta = np.full(len(hit_idx), math.log(1.6))   # start at OR 1.6 per A1 allele
    sign = np.where(rng.random(len(hit_idx)) < 0.5, 1.0, -1.0)   # risk on A1 or A2
    beta_sex, beta_age = math.log(1.3), math.log(1.05)          # males and older people at higher risk
    # One fixed pool of candidate people (common random numbers): every tuning round uses the
    # same people and the same random draws, so a larger effect always gives a stronger signal.
    pool_n = int(3 * n_target / min(args.prevalence, 0.5))
    p_sex = rng.integers(1, 3, pool_n)                                    # 1 = male, 2 = female
    p_age = np.clip(rng.normal(62, 9, pool_n), 35, 90)
    p_donor = rng.integers(0, len(eur), (len(hit_idx), pool_n))           # index into eur
    p_g = np.take_along_axis(hit_geno, p_donor, axis=1).astype(np.int8)
    p_g = np.where(p_g < 0, 0, p_g)
    p_u = rng.random(pool_n)
    for attempt in range(1, 61):
        b = beta * sign
        b0 = math.log(args.prevalence / (1 - args.prevalence)) - float(np.sum(b * 2 * hit_freq)) \
            - beta_sex * 0.5
        lin = b0 + (b[:, None] * p_g).sum(axis=0) + beta_sex * (p_sex == 1) + beta_age * (p_age - 62) / 5
        is_case = p_u < logistic(lin)
        case_ix = np.where(is_case)[0][:args.n_cases]
        ctrl_ix = np.where(~is_case)[0][:args.n_controls]
        if len(case_ix) < args.n_cases or len(ctrl_ix) < args.n_controls:
            sys.exit("ERROR: candidate pool too small; increase --prevalence or lower --n-cases")
        pvals = [allelic_p(p_g[h, case_ix], p_g[h, ctrl_ix]) for h in range(len(hit_idx))]
        weak = [h for h, pv in enumerate(pvals) if pv > args.target_p]
        log.info("Effect tuning round %d: ORs %s | allelic P %s", attempt,
                 ", ".join(f"{math.exp(x):.2f}" for x in beta), ", ".join(f"{pv:.1e}" for pv in pvals))
        if not weak:
            break
        for h in weak:
            beta[h] *= 1.05
    else:
        log.warning("Not all causal SNPs reach P < %g; consider more cases or --target-p", args.target_p)
    sel_ix = np.concatenate([case_ix, ctrl_ix])
    cases = [(int(p_sex[k]), float(p_age[k]), p_donor[:, k].copy(), p_g[:, k].copy()) for k in case_ix]
    controls = [(int(p_sex[k]), float(p_age[k]), p_donor[:, k].copy(), p_g[:, k].copy()) for k in ctrl_ix]
    people = cases + controls
    status = np.array([2] * len(cases) + [1] * len(controls), dtype=np.int8)
    sex = np.array([r[0] for r in people], dtype=np.int8)
    age = np.array([r[1] for r in people])
    hit_donor = np.array([r[2] for r in people])              # (n_target x n_hits), index into eur
    perm = rng.permutation(n_target)                           # mix cases and controls
    status, sex, age, hit_donor = status[perm], sex[perm], age[perm], hit_donor[perm]
    n = n_target
    iid = np.array([f"DUMMY{i + 1:05d}" for i in range(n)])

    # --- planted QC issues -----------------------------------------------------------
    truth = []
    reported_sex = sex.copy()
    ancestry = {}       # sample index -> donor pool of another super-population
    relatives = {}      # sample index -> sample index it is related to (first degree)
    duplicates = {}     # sample index -> sample index it duplicates
    miss_sample = rng.beta(1, 300, n)          # ~0.3% missing per sample on average
    if not args.no_qc_issues:
        pick = list(rng.permutation(n))
        def take(k):
            return [int(pick.pop()) for _ in range(k)]
        for i in take(6):
            reported_sex[i] = 3 - sex[i]
            truth.append(("sex_mismatch", iid[i], f"genetic sex {sex[i]}, reported {reported_sex[i]}"))
        for pool, name in ((afr, "AFR"), (asn, "ASN")):
            if len(pool) >= 10:
                for i in take(6):
                    ancestry[i] = pool
                    truth.append(("non_european", iid[i], f"ancestry {name}"))
        for i in take(5):
            j = int(pick.pop())
            relatives[i] = j
            truth.append(("first_degree_relative", iid[i], f"related to {iid[j]}"))
        for i in take(3):
            j = int(pick.pop())
            duplicates[i] = j
            sex[i], reported_sex[i] = sex[j], reported_sex[j]   # a duplicate has the same sex
            truth.append(("duplicate", iid[i], f"duplicate of {iid[j]}"))
        for i in take(15):
            miss_sample[i] = rng.uniform(0.05, 0.15)
            truth.append(("high_missingness_sample", iid[i], f"missing rate {miss_sample[i]:.3f}"))
    hwe_snps = set()
    miss_snp = rng.beta(1, 500, len(snps["row"]))
    spurious = {}       # SNP index -> artefact type
    if not args.no_qc_issues and args.n_spurious > 0:
        ok = np.isin(snps["chr"], list(AUTOSOMES))
        for c, lo, hi in EXCLUDED_FOR_HITS:
            ok &= ~((snps["chr"] == c) & (snps["bp"] >= lo) & (snps["bp"] <= hi))
        for h in hit_idx:   # keep clear of the real hits
            ok &= ~((snps["chr"] == snps["chr"][h]) & (np.abs(snps["bp"] - snps["bp"][h]) < 5_000_000))
        common = np.where(ok & (maf >= 0.20))[0]
        anyfreq = np.where(ok)[0]
        for kind, pool in (("differential_missingness", common), ("batch_error_controls", common),
                           ("rare_variant", anyfreq)):
            pool = np.setdiff1d(pool, list(spurious))
            for s_ in rng.choice(pool, min(args.n_spurious, len(pool)), replace=False):
                spurious[int(s_)] = kind
    if not args.no_qc_issues:
        auto_idx = np.where(np.isin(snps["chr"], list(AUTOSOMES)))[0]
        auto_idx = np.setdiff1d(auto_idx, list(hit_idx) + list(spurious))
        for s in rng.choice(auto_idx, min(200, len(auto_idx)), replace=False):
            hwe_snps.add(int(s))
            truth.append(("hwe_violation", snps["id"][s], "excess heterozygotes"))
        for s in rng.choice(auto_idx, min(int(0.01 * len(snps["row"])), len(auto_idx)), replace=False):
            miss_snp[s] = rng.uniform(0.03, 0.10)
            truth.append(("high_missingness_snp", snps["id"][s], f"missing rate {miss_snp[s]:.3f}"))

    # --- genotypes, chromosome by chromosome -------------------------------------------
    hit_chr_of = {int(snps["chr"][h]): (k, int(np.searchsorted(snps["bp"][snps["chr"] == snps["chr"][h]],
                                                                 snps["bp"][h])))
                  for k, h in enumerate(hit_idx)}
    sex_pool = {1: np.searchsorted(eur, eur_m), 2: np.searchsorted(eur, eur_f)}   # positions in eur
    with open(out + ".bed", "wb") as fbed, open(out + ".bim", "w") as fbim:
        fbed.write(BED_MAGIC)
        for c in CHR_ORDER:
            sel = np.where(snps["chr"] == c)[0]
            if len(sel) == 0:
                continue
            bp = snps["bp"][sel].astype(float)
            cols = np.concatenate([eur, afr, asn])
            donor_g = bed.read(snps["row"][sel], cols)        # SNPs x donors
            d_eur = donor_g[:, :len(eur)]
            d_afr = donor_g[:, len(eur):len(eur) + len(afr)]
            d_asn = donor_g[:, len(eur) + len(afr):]
            G = np.empty((len(sel), n), dtype=np.int8)
            for i in range(n):
                if c == 24:                                     # Y: males only, one donor
                    if sex[i] == 1:
                        G[:, i] = d_eur[:, rng.choice(sex_pool[1])]
                    else:
                        G[:, i] = -1
                    continue
                if c == 26:                                     # MT: one donor, whole chromosome
                    G[:, i] = d_eur[:, rng.integers(len(eur))]
                    continue
                if i in ancestry:                               # non-European sample
                    pool_g = d_afr if ancestry[i] is afr else d_asn
                    pool = np.arange(pool_g.shape[1])
                    if c in (23, 25):
                        psex = ref_sex[ancestry[i]]
                        pool = np.where(psex == sex[i])[0] if (psex == sex[i]).any() else pool
                else:
                    pool_g = d_eur
                    pool = sex_pool[int(sex[i])] if c in (23, 25) else np.arange(len(eur))
                starts = segment_plan(bp, seg_len, rng)
                ends = np.append(starts[1:], len(sel))
                donors = rng.choice(pool, len(starts))
                if c in hit_chr_of and i not in ancestry:      # the causal SNP keeps its sampled donor
                    k, pos = hit_chr_of[c]
                    seg = np.searchsorted(starts, pos, side="right") - 1
                    donors[seg] = hit_donor[i, k]
                for s0, s1, d in zip(starts, ends, donors):
                    G[s0:s1, i] = pool_g[s0:s1, d]
            if c in (23, 24):                                   # males are hemizygous: no hets
                male = sex == 1
                Gm = G[:, male]; Gm[Gm == 1] = -1; G[:, male] = Gm
            for i, j in relatives.items():                     # share about half of the segments
                if c in (23, 24, 25, 26):                       # autosomes only (sexes may differ)
                    continue
                starts = segment_plan(bp, seg_len, rng)
                ends = np.append(starts[1:], len(sel))
                for s0, s1 in zip(starts, ends):
                    if rng.random() < 0.5:
                        G[s0:s1, i] = G[s0:s1, j]
            for i, j in duplicates.items():                    # copy with 0.2% genotyping errors
                G[:, i] = G[:, j]
                err = rng.random(len(sel)) < 0.002
                G[err, i] = rng.integers(0, 3, int(err.sum()))
                if c in (23, 24) and sex[i] == 1:
                    G[err & (G[:, i] == 1), i] = -1
                if c == 24 and sex[i] == 2:
                    G[:, i] = -1
            for s_local, s_global in enumerate(sel):            # HWE: turn homozygotes into hets
                if int(s_global) in hwe_snps:
                    hom = np.where((G[s_local] == 0) | (G[s_local] == 2))[0]
                    flip = rng.choice(hom, int(0.3 * len(hom)), replace=False) if len(hom) else []
                    G[s_local, flip] = 1
            for s_local, s_global in enumerate(sel):            # spurious associations
                kind = spurious.get(int(s_global))
                if kind is None:
                    continue
                g = G[s_local]
                ctrl, case = np.where(status == 1)[0], np.where(status == 2)[0]
                if kind == "rare_variant":
                    # nearly monomorphic; minor-allele carriers are almost all cases (MAF < 1%)
                    major = 2 if np.mean(g[g >= 0]) >= 1 else 0
                    g[g >= 0] = major
                    carriers = np.concatenate([rng.choice(case, 24, replace=False), rng.choice(ctrl, 2, replace=False)])
                    g[carriers] = 1
                else:
                    minor_hom = 0 if np.mean(g[g >= 0]) >= 1 else 2
                    for strength in np.linspace(0.3, 1.0, 15):
                        t = g.copy()
                        if kind == "differential_missingness":
                            # in controls, minor homozygotes (and some hets) fail to be called
                            mh = ctrl[t[ctrl] == minor_hom]; ht = ctrl[t[ctrl] == 1]
                            t[mh[rng.random(len(mh)) < strength]] = -1
                            t[ht[rng.random(len(ht)) < 0.25 * strength]] = -1
                            t[ctrl[rng.random(len(ctrl)) < 0.04]] = -1
                        else:
                            # in controls, heterozygotes are called as major homozygotes
                            ht = ctrl[t[ctrl] == 1]
                            t[ht[rng.random(len(ht)) < strength]] = 2 - minor_hom
                        if allelic_p_status(t, status) < 1e-9:
                            break
                    g[:] = t
                p_sp = allelic_p_status(g, status)
                if p_sp > 5e-8:
                    log.warning("Spurious SNP %s (%s) only reaches P %.1e", snps["id"][s_global], kind, p_sp)
                truth.append(("spurious_" + kind, snps["id"][s_global],
                              f"chr{c}:{snps['bp'][s_global]}; allelic P before QC {p_sp:.1e}"))
                log.info("Spurious association (%s): %s chr%d:%d, P %.1e", kind, snps["id"][s_global], c,
                         snps["bp"][s_global], p_sp)
            # missingness: per sample and per SNP (in blocks, to limit memory)
            for b0_ in range(0, len(sel), 5000):
                ms = miss_snp[sel[b0_:b0_ + 5000]][:, None]
                pm = 1 - (1 - miss_sample[None, :]) * (1 - ms)
                blk = G[b0_:b0_ + 5000]
                blk[rng.random(blk.shape, dtype=np.float32) < pm] = -1
            fbed.write(encode_bed(G))
            for s in sel:
                fbim.write(f"{c}\t{snps['id'][s]}\t{snps['cm'][s]}\t{snps['bp'][s]}\t"
                           f"{snps['a1'][s]}\t{snps['a2'][s]}\n")
            log.info("Chromosome %d: %d SNPs written", c, len(sel))

    # --- fam, covariates, truth --------------------------------------------------------
    with open(out + ".fam", "w") as fh:
        for i in range(n):
            fh.write(f"{iid[i]}\t{iid[i]}\t0\t0\t{reported_sex[i]}\t{status[i]}\n")
    with open(out + ".covar", "w") as fh:
        fh.write("FID\tIID\tAGE\tSEX\n")
        for i in range(n):
            fh.write(f"{iid[i]}\t{iid[i]}\t{age[i]:.1f}\t{reported_sex[i]}\n")
    with open(out + ".truth.txt", "w") as fh:
        fh.write(f"# {VERSION_NAME} v{VERSION}, seed {args.seed}, reference {ref}\n")
        fh.write("type\tid\tdetails\n")
        for k, h in enumerate(hit_idx):
            risk = snps["a1"][h] if sign[k] > 0 else snps["a2"][h]
            fh.write(f"causal_snp\t{snps['id'][h]}\tchr{snps['chr'][h]}:{snps['bp'][h]}; risk allele {risk}; "
                     f"OR {math.exp(beta[k]):.2f} per risk allele; allelic P before planted QC issues {pvals[k]:.2e}\n")
        for t in truth:
            fh.write("\t".join(str(x) for x in t) + "\n")
    log.info("Done: %d cases, %d controls, %d SNPs -> %s.{bed,bim,fam,covar,truth.txt}",
             int((status == 2).sum()), int((status == 1).sum()), len(snps["row"]), out)


if __name__ == "__main__":
    main()
