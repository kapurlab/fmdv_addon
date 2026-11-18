# FMDV add-on for vsnp_gui

Foot-and-mouth disease virus as a vsnp_gui pathogen add-on (contract 1; see
bdtools' `docs/BUILDING_AN_ADDON.md`). A vsnp_gui project that names the
pathogen `fmdv` runs these steps around vsnp3:

| Step | What happens | Code |
|---|---|---|
| choose_reference | the closest of NanoFMDV's 79 lineage genomes, by a competitive minimap2 vote on their VP1 sequences, within the project's scope; distant and mixed flags | `fmdv/fmdv_choose_reference.py` |
| prepare_reads | amplicon primers clipped from ONT reads (NanoFMDV's binding rule, `samtools ampliconclip`) | `fmdv/fmdv_clip_primers.py` |
| vsnp3 Step 1 | stock vsnp3 on the chosen lineage reference: `_zc.vcf`, stats, BAM | vsnp_gui |
| after_sample | consensus from vsnp3's calls (depth under 10 to N) and its VP1 slice; VP1 typed by blastn against GenBank (serotype, topotype, lineage); the one-page report | `fmdv/fmdv_consensus.py`, `fmdv_vp1_type.py`, `fmdv_sample_report.py` |
| after_run | the run report for the outbreak team | `fmdv/fmdv_run_report.py` |
| action: VP1 tree | one serotype's samples with the panel and a GenBank context set (mafft + RAxML), neighbourhood trees, variable-site tables | `fmdv/fmdv_vp1_tree.py`, `fmdv_vp1_tables.py` |
| action: retype | VP1 typing again, then the reports | `fmdv/fmdv_vp1_type.py` |
| Step 2 | stock vsnp3, one comparison per lineage reference; optional per-reference databases | `deploy/build_step2_databases.sh` |

The FMDV code is Vivek Kapur's FMDV mode (kapurlab/vsnp_gui#14), moved here
and pointed at the add-on's folders (`fmdv/layout.py`); `docs/` carries its
design notes, measurements, deployment plan and walkthrough.

## Library

`bdtools install fmdv_addon` builds the env, then `deploy/build_library.sh`
builds the library under `<db root>/addons/fmdv`:

- NanoFMDV (Shaw et al. 2025, github.com/rjorton/nanofmdv) at a pinned commit:
  79 lineage genomes, their VP1 panel, 11,153 GenBank records and the primer
  scheme. They are read at build time and never redistributed here (NanoFMDV
  carries no licence file).
- Each genome's GenBank record and GFF3 from NCBI, rewritten so the 12 mature
  proteins are the CDS features (`VP1:H45Q`, not polyprotein numbering).
  Offline builds skip this and say so. `NCBI_EMAIL`, if set, is the contact
  address sent to NCBI.
- Per-serotype VP1 context sets (BLAST), every reference folder, VP1
  coordinates, primer BEDs, the typing database and `scopes.json`, all built
  up front: the library is read-only at run time.

Offline sites: stage a NanoFMDV checkout at the pinned commit and set
`FMDV_NANOFMDV_DIR` before installing.

## Checking it

```bash
env/bin/python tests/test_fmdv_consensus.py      # and the other tests/test_*.py
bin/bdtools addon-check fmdv                     # from bdtools: manifest, library, every hook on the fixture
```

`tests/known_answer/SYN_answer_key/` is the answer key of FMDV mode's simulated
MinKNOW run (11 barcodes); `docs/FMDV_MODE_HANDOFF.md` lists what was verified
and what is not done.
