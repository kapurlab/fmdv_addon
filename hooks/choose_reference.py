"""choose_reference: the closest FMDV lineage genome for this sample.

Competitive minimap2 of the reads against the VP1 panel of the library's
lineage genomes, within the project's scope (fmdv_choose_reference.py), with
whole genomes as the fallback. Writes the chooser's record
(fmdv_reference.json: the vote, the runner-up, identity, serotype share and
the distant / mixed flags) beside reference.json.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import addon_sdk as sdk  # noqa: E402
import fmdv_run as F  # noqa: E402


def main():
    ctx = sdk.load_context()
    out, s = ctx.out_dir, ctx.sample
    p = F.run("fmdv_choose_reference.py", "--reads", *s["reads"], "--lib", ctx.library,
              "--scope", ctx.scope or "FMDV", "--sample-dir", out, "--threads", ctx.threads, check=False)
    rec = F.load(out / "fmdv_reference.json")
    folder = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
    if p.returncode != 0 or not folder:
        sdk.fail(rec.get("error") or f"no lineage genome chosen (chooser exited {p.returncode})",
                 out=out, name="reference.json")
    chosen = rec.get("chosen") or {}
    sdk.write_reference(ctx, Path(folder), serotype=chosen.get("serotype"), lineage=chosen.get("lineage"),
                        identity=rec.get("identity"), distant=rec.get("distant"), mixed=rec.get("mixed"),
                        runner_up=rec.get("runner_up"), method=rec.get("method"))


if __name__ == "__main__":
    main()
