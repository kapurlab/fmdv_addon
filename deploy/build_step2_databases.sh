#!/usr/bin/env bash
# Step 2 reference databases for chosen lineage references (optional).
#
#   VSNP3_BIN=<vsnp_gui's vsnp3 env>/bin bash deploy/build_step2_databases.sh [--lib <library>] <reference> [...]
#
# For each reference: every other library genome called against it with
# vsnp3 (FASTA mode), copied into <library>/vcf_db_folders/<reference>/
# (FMDV_all, and one database per serotype), and the reference's
# define_filter.xlsx rewritten with one defining-SNP group per topotype.
# vsnp_gui lists those databases on Step 2's Build tab for a comparison on that
# reference. 78 vsnp3 runs per reference: build the references a site uses,
# not all 79 (from FMDV mode: fmdv_panel_build.sh, fmdv_panel_register.py,
# fmdv_define_snps.py).
#
# The library is otherwise read-only at run time; this is an administrator's
# step, run by whoever owns the library. vsnp_gui must be restarted, or its
# reference list refreshed, to see new databases.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
LIB=""
if [[ "${1:-}" == "--lib" ]]; then LIB="$2"; shift 2; fi
LIB="${LIB:-$(cat "${HERE}/.library_path" 2>/dev/null || true)}"
[[ -n "${LIB}" && -f "${LIB}/lineages.json" ]] || { echo "error: no FMDV library (pass --lib, or install the add-on first)" >&2; exit 1; }
[[ $# -ge 1 ]] || { echo "usage: build_step2_databases.sh [--lib <library>] <reference> [...]" >&2; exit 1; }
PY="${HERE}/env/bin/python"; [[ -x "${PY}" ]] || PY="$(command -v python3)"
for REF in "$@"; do
  [[ -d "${LIB}/reference_options/${REF}" ]] || { echo "error: ${REF} is not a library reference" >&2; exit 1; }
  echo "== ${REF}: calling the other library genomes against it"
  FMDV_LIB="${LIB}" bash "${HERE}/fmdv/fmdv_panel_build.sh" "${REF}"
  "${PY}" "${HERE}/fmdv/fmdv_panel_register.py" "${REF}" --lib "${LIB}" --no-register
  "${PY}" "${HERE}/fmdv/fmdv_define_snps.py" --lib "${LIB}" --ref "${REF}"
done
echo "Step 2 databases built under ${LIB}/vcf_db_folders/"
