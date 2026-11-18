"""Finish the FMDV library so nothing is written into it at run time.

    python fmdv/library_prebuild.py --lib <library> [--primers <library>/primers/default.fasta]

In vsnp_gui's FMDV mode each of these was made the first time a run needed it,
inside the library; an add-on's library is read-only at run time (a shared
site library is not writable by the users who run samples), so all of them
are made here, once, by the installer:

  reference_options/<genome>/    every lineage genome as a vsnp3 reference folder
                                 (fmdv_reflib.materialize), not only the ones
                                 some sample chose
  .../VP1_coords.json            VP1's interval on each genome (fmdv_consensus)
  .../primers_<set>_<sha>.bed    each genome's primer binding sites (fmdv_clip_primers)
  vp1_context/_typing/all_vp1.*  the blastn typing database (fmdv_vp1_type)
  scopes.json                    the project form's scope picker: FMDV, each
                                 serotype, each lineage, each genome
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fmdv_clip_primers as CP  # noqa: E402
import fmdv_consensus as CO  # noqa: E402
import fmdv_reflib as RL  # noqa: E402
import fmdv_vp1_type as VT  # noqa: E402

SCOPE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./:+-]{0,127}")
REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}")


def scopes(index: dict) -> dict:
    """{"label", "default", "options": [{value, label, children}]} for the
    scope grammar fmdv_reflib.genomes_in_scope reads."""
    by_safe = {g["safe"]: g for g in index["genomes"]}
    sero_nodes = []
    for sero in sorted(index["tree"]):
        lineages = index["tree"][sero]
        lin_nodes = []
        for lin in sorted(lineages):
            genomes = [{"value": f"genome:{s}",
                        "label": f"{s} ({by_safe[s].get('isolate') or by_safe[s].get('accession')}"
                                 f"{', ' + str(by_safe[s].get('year')) if by_safe[s].get('year') else ''})"}
                       for s in sorted(lineages[lin])]
            value = f"{sero}/{lin}"
            if lin != "(unassigned)" and SCOPE_RE.fullmatch(value) and ".." not in value:
                lin_nodes.append({"value": value, "label": f"{sero} {lin} (closest of {len(genomes)})",
                                  "children": genomes})
            else:
                lin_nodes.extend(genomes)
        n = sum(len(v) for v in lineages.values())
        sero_nodes.append({"value": sero, "label": f"{sero} (closest of {n})", "children": lin_nodes})
    return {"label": "Scope", "default": "FMDV",
            "options": [{"value": "FMDV", "label": f"Any FMDV lineage (closest of {len(index['genomes'])})",
                         "children": sero_nodes}]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lib", required=True)
    ap.add_argument("--primers", help="primer set FASTA (default <lib>/primers/default.fasta, if present)")
    ap.add_argument("--min-fit", type=float, default=0.8)
    a = ap.parse_args()
    lib = Path(a.lib).resolve()
    index = RL.load(lib)
    primers = Path(a.primers) if a.primers else lib / "primers" / "default.fasta"
    bad = [g["safe"] for g in index["genomes"] if not REF_RE.fullmatch(g["safe"])]
    if bad:
        print("library_prebuild: genome names vsnp3 cannot keep as given: " + ", ".join(bad), file=sys.stderr)
        return 2
    tmp = Path(tempfile.mkdtemp(prefix="fmdv_prebuild_"))
    vp1_ok = beds = 0
    try:
        for g in index["genomes"]:
            folder = RL.materialize(lib, g["safe"])
            fasta = folder / f"{g['safe']}.fasta"
            if CO.vp1_coords(lib, g["safe"], fasta, tmp):
                vp1_ok += 1
            if primers.is_file():
                CP.primer_bed(fasta, primers, folder, a.min_fit)
                beds += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    makeblastdb = shutil.which("makeblastdb")
    if makeblastdb and (lib / "vp1_context").is_dir():
        VT.ensure_db(lib, makeblastdb)
        typing = "typing database built"
    else:
        typing = "NO typing database (makeblastdb or vp1_context missing)"
    (lib / "scopes.json").write_text(json.dumps(scopes(index), indent=1))
    print(f"library_prebuild: {len(index['genomes'])} reference folders, VP1 located on {vp1_ok}, "
          f"primer BEDs for {beds}, {typing}, scopes.json written")
    return 0 if vp1_ok == len(index["genomes"]) else 1


if __name__ == "__main__":
    sys.exit(main())
