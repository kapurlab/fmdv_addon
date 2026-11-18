#!/usr/bin/env bash
# Build the FMDV reference library into the folder bdtools names.
#
#   bash deploy/build_library.sh <library dir>
#
# bdtools runs this after building the add-on's env (its bin/ first on PATH)
# with <db root>/addons/fmdv as the folder, and records it in .library_path.
# Idempotent: a library already built for this LIBRARY_VERSION is left alone
# (delete LIBRARY_VERSION, or the folder, to rebuild). No sudo; nothing is
# written outside the library folder.
#
# Sources (read at build time, never redistributed in this repository):
#   NanoFMDV (Shaw et al. 2025, github.com/rjorton/nanofmdv), pinned below:
#     NANOFMDV-PIPELINE/Refs/fmdv.fasta              79 lineage genomes
#     NANOFMDV-PIPELINE/Refs/fmdv_vp1.fasta          their VP1 sequences
#     NANOFMDV-PIPELINE/Refs/BLAST/fmdv-gbbase.fasta 11,153 GenBank records
#     NANOFMDV-PIPELINE/primers.fasta                the amplicon primer scheme
#   NCBI E-utilities: each genome's GenBank record and GFF3, for the Step 2
#     annotation row and IGV's gene track (skipped, with a note, when offline).
#
# Offline sites: stage a NanoFMDV checkout at the pinned commit and export
# FMDV_NANOFMDV_DIR=<it> before `bdtools install fmdv_addon`. NCBI_EMAIL, if
# set, is sent to NCBI as the contact address (NCBI asks scripted clients for
# one); nothing else identifies the site.
set -euo pipefail
LIB="${1:?usage: build_library.sh <library dir>}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="1"
NANOFMDV_REPO="https://github.com/rjorton/nanofmdv.git"
NANOFMDV_COMMIT="400ffaf1c74ca97b70f5fff1a33ebcb5ee3e21a7"
THREADS="${FMDV_THREADS:-4}"
PY="$(command -v python)"

if [[ -f "${LIB}/LIBRARY_VERSION" && "$(cat "${LIB}/LIBRARY_VERSION")" == "${VERSION}" ]]; then
  echo "FMDV library ${LIB} is current (version ${VERSION})"
  exit 0
fi
mkdir -p "${LIB}"
rm -f "${LIB}/LIBRARY_VERSION"

# 1. NanoFMDV, at the pinned commit
SRC="${FMDV_NANOFMDV_DIR:-${LIB}/_source/nanofmdv}"
if [[ ! -f "${SRC}/NANOFMDV-PIPELINE/Refs/fmdv.fasta" ]]; then
  echo "fetching NanoFMDV ${NANOFMDV_COMMIT:0:7} -> ${SRC}"
  rm -rf "${SRC}"
  mkdir -p "$(dirname "${SRC}")"
  git clone --quiet "${NANOFMDV_REPO}" "${SRC}" || {
    echo "error: could not clone ${NANOFMDV_REPO}. Offline? Stage a checkout and set FMDV_NANOFMDV_DIR." >&2
    exit 1
  }
  git -C "${SRC}" -c advice.detachedHead=false checkout --quiet "${NANOFMDV_COMMIT}"
fi
have="$(git -C "${SRC}" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "${have}" != "${NANOFMDV_COMMIT}" ]]; then
  echo "warning: NanoFMDV at ${SRC} is ${have}, not the pinned ${NANOFMDV_COMMIT}" >&2
fi
REFS="${SRC}/NANOFMDV-PIPELINE/Refs"

# 2. Genomes, hierarchy, VP1 and genome panels
"${PY}" "${HERE}/fmdv/fmdv_reflib.py" build --refs "${REFS}/fmdv.fasta" --lib "${LIB}" --vp1 "${REFS}/fmdv_vp1.fasta"

# 3. The primer scheme (default.fasta is the set clipping uses)
mkdir -p "${LIB}/primers"
cp "${SRC}/NANOFMDV-PIPELINE/primers.fasta" "${LIB}/primers/default.fasta"

# 4. GenBank and GFF3 per genome, rewritten by mature protein (VP1:H45Q, not
#    polyprotein numbering). Needs NCBI; a site that builds offline gets
#    reference folders without annotation and a note saying so.
if "${PY}" "${HERE}/fmdv/fmdv_reflib.py" annotations --lib "${LIB}"; then
  ANNOT="annotated (GenBank + GFF3 by mature protein)"
else
  ANNOT="NOT annotated: NCBI unreachable; re-run the build online to add it"
  echo "warning: ${ANNOT}" >&2
fi

# 5. Per-serotype VP1 context sets from the GenBank collection (BLAST)
"${PY}" "${HERE}/fmdv/fmdv_vp1_context.py" --source "${REFS}/BLAST/fmdv-gbbase.fasta" --lib "${LIB}" --threads "${THREADS}"

# 6. Everything a run would otherwise write into the library: every reference
#    folder, VP1 coordinates, primer BEDs, the typing database, scopes.json
"${PY}" "${HERE}/fmdv/library_prebuild.py" --lib "${LIB}" --primers "${LIB}/primers/default.fasta"

cat > "${LIB}/LIBRARY_NOTES.txt" <<EOF
FMDV add-on library, version ${VERSION}
NanoFMDV: ${NANOFMDV_REPO} @ ${have}
Annotation: ${ANNOT}
Built: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Step 2 reference databases (vcf_db_folders/<reference>/) are built per reference
on request: deploy/build_step2_databases.sh <reference> [...]
EOF
printf '%s\n' "${VERSION}" > "${LIB}/LIBRARY_VERSION"
echo "FMDV library built: ${LIB}"
