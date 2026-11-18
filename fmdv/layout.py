"""Where the FMDV add-on's files live in a vsnp_gui project.

vsnp_gui gives each pathogen add-on its own folder in the project
(docs/BUILDING_AN_ADDON.md in bdtools), so nothing here writes into vsnp3's
step1/ or step2/:

  <project>/pathogen/fmdv/                     run report, summary.json
  <project>/pathogen/fmdv/samples/<sample>/    per sample: the chooser's answer,
                                               consensus, VP1 typing, report
  <project>/pathogen/fmdv/runs/<stamp>_<action>/  VP1 trees and their tables

In vsnp_gui's FMDV mode (kapurlab/vsnp_gui#14) the same files sat in
step1/<sample>/ and step2/<stamp>_VP1-tree*/; every script that looked there
asks this module instead.
"""
import re
from pathlib import Path

ADDON_ID = "fmdv"


def pathogen_root(project: Path) -> Path:
    return Path(project) / "pathogen" / ADDON_ID


def samples_root(project: Path) -> Path:
    return pathogen_root(project) / "samples"


def runs_root(project: Path) -> Path:
    return pathogen_root(project) / "runs"


def project_of(sample_dir: Path) -> Path:
    """<project> from <project>/pathogen/fmdv/samples/<sample>."""
    return Path(sample_dir).resolve().parents[3]


def sample_dirs(project: Path, names=None, marker: str = "fmdv_reference.json"):
    root = samples_root(project)
    if not root.is_dir():
        return []
    return sorted(d for d in root.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))
                  and (d / marker).is_file() and (not names or d.name in names))


def tree_runs(project: Path):
    """VP1 tree runs, newest first: vsnp_gui names an action's run folder
    <stamp>_vp1_tree[-<SEROTYPE>]; FMDV mode's were <stamp>_VP1-tree[-<SEROTYPE>]."""
    root = runs_root(project)
    if not root.is_dir():
        return []
    return sorted((d for d in root.iterdir() if d.is_dir() and TREE_RUN.search(d.name)), reverse=True)


TREE_RUN = re.compile(r"vp1[-_]tree", re.I)
# The serotype a tree run was restricted to, from its folder name.
TREE_SEROTYPE = re.compile(r"vp1[-_]tree-([A-Za-z0-9]+)$", re.I)
