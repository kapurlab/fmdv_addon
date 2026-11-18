"""Action: type every sample's VP1 again (a new typing database, or a sample
re-run), then rewrite the reports."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import addon_sdk as sdk  # noqa: E402
import fmdv_run as F  # noqa: E402


def main():
    ctx = sdk.load_context()
    F.run("fmdv_vp1_type.py", "--project", ctx.project_dir, "--lib", ctx.library, "--threads", ctx.threads,
          "--force", check=False)
    F.run("fmdv_sample_report.py", "--project", ctx.project_dir, "--lib", ctx.library, check=False)
    F.run("fmdv_run_report.py", "--project", ctx.project_dir, "--lib", ctx.library, check=False)
    sdk.write_action(ctx, [], summary="VP1 typing and reports rewritten; Re-run add-on steps refreshes the Results rows")


if __name__ == "__main__":
    main()
