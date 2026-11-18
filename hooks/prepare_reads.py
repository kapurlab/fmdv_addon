"""prepare_reads: clip the amplicon primers from ONT reads (NanoFMDV's rule).

The primer binding sites are found once per reference and primer set at
library build time (library_prebuild.py); samtools ampliconclip removes them
here. Paired short reads are passed through: clipping each mate on its own
would let the pairs drift apart, and the trial reads carried no primers.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import addon_sdk as sdk  # noqa: E402
import fmdv_run as F  # noqa: E402


def main():
    ctx = sdk.load_context()
    s, out = ctx.sample, ctx.out_dir
    reads = s["reads"]
    primers = ctx.library / "primers" / "default.fasta"
    if len(reads) != 1 or not primers.is_file():
        sdk.log("primer clipping: " + ("paired reads are passed through" if len(reads) != 1
                                        else "no primer set in the library"))
        sdk.write_reads(ctx, [Path(r) for r in reads], clipped=False)
        return
    p = F.run("fmdv_clip_primers.py", "--reads", reads[0], "--ref-dir", s["reference_dir"],
              "--primers", primers, "--sample-dir", out, "--threads", ctx.threads, check=False)
    clipped = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
    if p.returncode != 0 or not clipped or not Path(clipped).is_file():
        sdk.fail(f"primer clipping failed (exit {p.returncode})")
    sdk.write_reads(ctx, [Path(clipped)], clipped=True, primers=str(primers))


if __name__ == "__main__":
    main()
