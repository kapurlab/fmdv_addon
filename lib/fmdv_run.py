"""How the FMDV hooks call the FMDV scripts (fmdv/): one place for the
interpreter, the log, and turning the scripts' JSON into Results rows.

The scripts are Vivek Kapur's FMDV mode (kapurlab/vsnp_gui#14), run as they
were written; the hooks only hand them the add-on's folders.
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

FMDV = Path(__file__).resolve().parent.parent / "fmdv"


def run(script: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run fmdv/<script> with this env's python; its stderr goes to the log
    (the sample's run_step1.log, or the job log for an action)."""
    cmd = [sys.executable, str(FMDV / script), *[str(a) for a in args]]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.stderr:
        sys.stdout.write(p.stderr if p.stderr.endswith("\n") else p.stderr + "\n")
        sys.stdout.flush()
    if check and p.returncode != 0:
        raise RuntimeError(f"{script} exited {p.returncode}")
    return p


def load(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def flags(ref: Dict[str, Any]) -> List[str]:
    """The chooser's two review signals (FMDV mode's _fmdv_flag_qc_rows):
    distant (the closest lineage genome is still far from the reads) and
    mixed (a second serotype holds 5% or more of the VP1 reads)."""
    reasons = []
    if ref.get("distant"):
        ident = ref.get("identity")
        reasons.append("distant reference" + (f", identity {ident:.2f}" if isinstance(ident, (int, float)) else ""))
    if ref.get("mixed"):
        share = ref.get("serotype_share") or {}
        top = ", ".join(f"{k} {v:.0%}" for k, v in list(share.items())[:3])
        reasons.append("mixed serotypes" + (f" ({top})" if top else ""))
    return reasons


def metrics(out: Path, qc_row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """One sample's Results row, from the chooser, the consensus and the VP1
    typing (the column set of FMDV mode's Step 1 Results)."""
    ref, cons, typ = load(out / "fmdv_reference.json"), load(out / "fmdv_consensus.json"), load(out / "fmdv_vp1_type.json")
    chosen = ref.get("chosen") or {}
    best = typ.get("best") or {}
    row = qc_row or {}
    m: Dict[str, Any] = {
        "serotype": chosen.get("serotype"),
        "lineage": chosen.get("lineage"),
        "reference": chosen.get("safe"),
        "identity": ref.get("identity"),
        "topotype": typ.get("topotype"),
        "vp1_lineage": typ.get("lineage"),
        "vp1_identity": typ.get("identity"),
        "vp1_nearest": " ".join(x for x in (best.get("accession"), best.get("isolate"), best.get("country"),
                                            str(best.get("year") or "")) if x),
        "vp1_status": typ.get("status"),
        "genome_called": cons.get("called_percent"),
        "vp1_called": cons.get("vp1_called_percent"),
        "consensus_length": cons.get("length"),
        "distant": bool(ref.get("distant")),
        "mixed": bool(ref.get("mixed")),
    }
    m["reads"] = _int(row.get("R1 Read Count"))
    em = re.match(r"\s*([0-9.]+)\s*%", str(row.get("Long-read Error Rate") or ""))
    m["error_rate"] = float(em.group(1)) if em else None
    tm = re.search(r"(\d[\d,]*) thin calls", str(row.get("Long-read Calls Limited to N") or ""))
    m["thin_calls"] = int(tm.group(1).replace(",", "")) if tm else None
    return m


def _int(v: Any) -> Optional[int]:
    try:
        return int(str(v).replace(",", "").split(".")[0])
    except (TypeError, ValueError):
        return None


def sample_files(out: Path, sample: str) -> List[Dict[str, str]]:
    import addon_sdk as sdk
    files = []
    for name, kind, label in ((f"{sample}_FMDV_report.pdf", "report", "FMDV report (PDF)"),
                              (f"{sample}_FMDV_report.html", "report", "FMDV report"),
                              (f"{sample}_VP1.fasta", "fasta", "VP1 consensus"),
                              (f"{sample}_consensus.fasta", "fasta", "Genome consensus"),
                              ("fmdv_vp1_type.json", "json", "VP1 typing"),
                              ("fmdv_reference.json", "json", "Reference choice")):
        p = out / name
        if p.is_file():
            files.append(sdk.file_entry(p, kind, label))
    return files
