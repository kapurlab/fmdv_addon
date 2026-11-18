"""after_sample: consensus, VP1 typing, the sample's report and Results row.

  fmdv_consensus.py   vsnp3's calls on the reference, a pileup check, depth
                      under 10 to N; the VP1 slice (reads the Step 1 folder,
                      writes here)
  fmdv_vp1_type.py    blastn of the VP1 consensus: serotype, topotype, lineage
  fmdv_sample_report  the one-page report (HTML, PDF)

The QC verdict vsnp_gui computed for the sample, joined with the chooser's
distant / mixed flags, is kept as fmdv_qc.json so the report says what the
Results table says.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import addon_sdk as sdk  # noqa: E402
import fmdv_run as F  # noqa: E402


LEVELS = {"pass": 0, "review": 1, "fail": 2}


def main():
    ctx = sdk.load_context()
    s, out = ctx.sample, ctx.out_dir
    name = s["name"]
    lib = ctx.library
    F.run("fmdv_consensus.py", "--sample-dir", s["step1_dir"], "--out-dir", out, "--sample", name,
          "--lib", lib, check=False)
    F.run("fmdv_vp1_type.py", "--sample-dir", out, "--lib", lib, "--threads", ctx.threads, check=False)
    reasons = F.flags(F.load(out / "fmdv_reference.json"))
    level = "review" if reasons else "pass"
    qc = s.get("qc") or {}
    verdict = dict(qc.get("verdict") or {"level": "pass", "reasons": []})
    if LEVELS[level] > LEVELS.get(verdict.get("level"), 0):
        verdict["level"] = level
    verdict["reasons"] = list(verdict.get("reasons") or []) + reasons
    (out / "fmdv_qc.json").write_text(json.dumps({"row": qc.get("row"), "verdict": verdict,
                                                  "thresholds": qc.get("thresholds")}, indent=1, default=str))
    F.run("fmdv_sample_report.py", "--sample-dir", out, "--lib", lib, check=False)
    metrics = F.metrics(out, qc.get("row"))
    if metrics.get("vp1_status") and metrics["vp1_status"] != "typed":
        reasons.append(f"VP1 not typed: {metrics['vp1_status']}")
        level = "review"
    sdk.write_result(ctx, metrics, level=level, reasons=reasons, files=F.sample_files(out, name))


if __name__ == "__main__":
    main()
