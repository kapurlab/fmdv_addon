"""after_run: the run report for the outbreak team, and the run summary."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import addon_sdk as sdk  # noqa: E402
import fmdv_run as F  # noqa: E402


def main():
    ctx = sdk.load_context()
    F.run("fmdv_run_report.py", "--project", ctx.project_dir, "--lib", ctx.library, check=False)
    rows = ctx.get("samples") or []
    files = [sdk.file_entry(p, "report", label) for p, label in
             ((ctx.out_dir / "FMDV_run_report.pdf", "Run report (PDF)"),
              (ctx.out_dir / "FMDV_run_report.html", "Run report")) if p.is_file()]
    by_sero = {}
    for r in rows:
        sero = (r.get("metrics") or {}).get("serotype") or "?"
        by_sero[sero] = by_sero.get(sero, 0) + 1
    text = f"{len(rows)} sample(s): " + ", ".join(f"{n} {k}" for k, n in sorted(by_sero.items()))
    sdk.write_summary(ctx, [{"sample": r.get("sample"), "serotype": (r.get("metrics") or {}).get("serotype"),
                             "lineage": (r.get("metrics") or {}).get("vp1_lineage") or (r.get("metrics") or {}).get("lineage"),
                             "level": (r.get("flags") or {}).get("level")} for r in rows],
                      files=files, text=text)


if __name__ == "__main__":
    main()
