"""Action: the VP1 tree of one serotype's samples with the lineage panel and a
GenBank context set (mafft + RAxML), its neighbourhood trees and variable-site
tables; then every sample report and the run report are rewritten with it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import addon_sdk as sdk  # noqa: E402
import fmdv_run as F  # noqa: E402


def main():
    ctx = sdk.load_context()
    run = ctx.out_dir
    sero = ctx.params.get("serotype") or ""
    args = ["--project", ctx.project_dir, "--lib", ctx.library, "--out", run, "--threads", ctx.threads]
    if sero:
        args += ["--serotype", sero]
    p = F.run("fmdv_vp1_tree.py", *args, check=False)
    vp1 = run / "VP1"
    trees = sorted(vp1.glob("VP1_*.tre"))
    if p.returncode != 0 or not trees:
        sdk.write_action(ctx, [], summary=f"no tree (vp1_tree exited {p.returncode}; see the job log)", status="failed")
        raise SystemExit(1)
    F.run("fmdv_sample_report.py", "--project", ctx.project_dir, "--lib", ctx.library, check=False)
    F.run("fmdv_run_report.py", "--project", ctx.project_dir, "--lib", ctx.library, check=False)
    files = []
    hood = vp1 / "VP1_neighbourhood.tre"
    if hood.is_file():
        files.append(sdk.file_entry(hood, "tree", "Neighbourhood tree"))
    files += [sdk.file_entry(t, "tree", "Full tree") for t in trees
              if t.name != "VP1_neighbourhood.tre" and not t.name.startswith("VP1_neighbourhood_")]
    files += [sdk.file_entry(t, "table", t.stem.replace("VP1_", "").replace("_", " ")) for t in sorted(vp1.glob("VP1_*_table_*.xlsx"))]
    summ = F.load(vp1 / "vp1_tree.json")
    n = len(summ.get("samples_included") or [])
    sdk.write_action(ctx, files, summary=f"VP1 tree{' of ' + sero if sero else ''}: {n} sample(s), "
                                         f"{summ.get('panel_sequences', '?')} panel and context sequences")


if __name__ == "__main__":
    main()
