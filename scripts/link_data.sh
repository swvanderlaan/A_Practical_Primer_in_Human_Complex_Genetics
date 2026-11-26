#!/usr/bin/env bash
#
# link_data.sh
#
# Link the course data on Google Drive into the repository's data/ folder, so the
# book (Quarto render) and the exercise tests find it under data/... without a copy.
# The small tracked files in data/ (scripts/, support/, readme*.txt) stay as they are;
# only the large data folders become symbolic links (ignored by git).
#
# Expected layout (either works):
#   <data-dir>/course_input/{rawdata,gwas,ref_1kg_phase1_all,...}  and  <data-dir>/reference_results/dummy_project
#   <data-dir>/{rawdata,gwas,ref_1kg_phase1_all,dummy_project,...}
#
# Usage:
#   scripts/link_data.sh -d "<Google Drive>/.../A_primer_in_Human_Cardiovascular_Genetics_data" \
#                        [-w "<Google Drive>/.../A_primer_in_Human_Cardiovascular_Genetics_data_wtccc1"] [-r <repo>]
#
# MIT License
#
# Copyright (c) 2026 Sander W. van der Laan | s.w.vanderlaan [at] gmail [dot] com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

VERSION_NAME="link_data"
VERSION="1.0.0"
VERSION_DATE="2026-11-26"

set -euo pipefail

usage() {
  cat <<EOF
${VERSION_NAME} v${VERSION} (${VERSION_DATE})
Link the course data on Google Drive into <repo>/data/.

  -d DIR   course data folder on Google Drive (required)
  -w DIR   WTCCC1 data folder (optional; restricted data, never commit it)
  -r DIR   repository folder (default: the folder above this script)
  -h       show this help
EOF
}

DATA_DIR=""; WTCCC1_DIR=""
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
while getopts "d:w:r:h" opt; do
  case "${opt}" in
    d) DATA_DIR="${OPTARG}" ;;
    w) WTCCC1_DIR="${OPTARG}" ;;
    r) REPO_DIR="${OPTARG}" ;;
    h) usage; exit 0 ;;
    *) usage; exit 1 ;;
  esac
done
[[ -z "${DATA_DIR}" ]] && { usage; exit 1; }
[[ -d "${DATA_DIR}" ]] || { echo "ERROR: ${DATA_DIR} is not a folder"; exit 1; }

TARGET="${REPO_DIR}/data"
mkdir -p "${TARGET}"
LOG="${TARGET}/$(date +%Y%m%d)_${VERSION_NAME}.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG}"; }

log "${VERSION_NAME} v${VERSION} (${VERSION_DATE})"
log "Course data: ${DATA_DIR}"
log "Repository:  ${REPO_DIR}"

# the course input may sit in a course_input/ subfolder; the executed book in reference_results/
INPUT_DIR="${DATA_DIR}"
[[ -d "${DATA_DIR}/course_input" ]] && INPUT_DIR="${DATA_DIR}/course_input"
RESULTS_DIR="${DATA_DIR}"
[[ -d "${DATA_DIR}/reference_results" ]] && RESULTS_DIR="${DATA_DIR}/reference_results"

link_one() {
  # link_one <source folder> <name in data/>
  local src="$1" name="$2" dst="${TARGET}/$2"
  if [[ ! -d "${src}" ]]; then
    log "skip ${name}: ${src} not found"
    return
  fi
  if [[ -L "${dst}" ]]; then
    ln -sfn "${src}" "${dst}"
    log "updated link data/${name} -> ${src}"
  elif [[ -e "${dst}" ]]; then
    log "skip ${name}: data/${name} already exists and is not a link (left untouched)"
  else
    ln -s "${src}" "${dst}"
    log "linked data/${name} -> ${src}"
  fi
}

for name in rawdata gwas ref_1kg_phase1_all ref_hapmap3; do
  link_one "${INPUT_DIR}/${name}" "${name}"
done
link_one "${RESULTS_DIR}/dummy_project" "dummy_project"
if [[ -n "${WTCCC1_DIR}" ]]; then
  if [[ -d "${WTCCC1_DIR}/wtccc1" ]]; then link_one "${WTCCC1_DIR}/wtccc1" "wtccc1"; else link_one "${WTCCC1_DIR}" "wtccc1"; fi
fi

# the small tracked files (scripts/, support/, readmes) come from git, not from the Drive
if [[ ! -d "${TARGET}/scripts" || ! -d "${TARGET}/support" ]]; then
  log "data/scripts or data/support is missing: restore them from git with 'git checkout -- data/'"
fi
log "Done. Check with: ls -l ${TARGET}"
