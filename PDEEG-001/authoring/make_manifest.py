"""Write environment/source_manifest.json from a local copy of OpenNeuro ds002778.

Only the files the task stages are listed: dataset-level metadata, and for the 16 control
(ses-hc) and 15 off-medication (ses-off) recordings the BDF plus its sidecars. The on-medication
sessions are not staged.

    python authoring/make_manifest.py <ds002778_dir>
"""
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
task = Path(__file__).resolve().parents[1]
keys = ["README", "CHANGES", "dataset_description.json", "participants.tsv", "participants.json"]
for p in sorted(root.glob("sub-*/ses-*/eeg/*")):
    rel = p.relative_to(root).as_posix()
    ses = p.parts[-3]
    if ses in ("ses-hc", "ses-off") and p.name.endswith(("_eeg.bdf", "_eeg.json", "_channels.tsv")):
        keys.append(rel)
files = []
for k in keys:
    b = (root / k).read_bytes()
    files.append({"path": k, "url": f"https://s3.amazonaws.com/openneuro.org/ds002778/{k}",
                  "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
manifest = {"dataset_id": "ds002778", "dataset_doi": "10.18112/openneuro.ds002778.v1.0.4", "license": "CC0",
            "captured": "2026-10-08", "n_files": len(files), "total_bytes": sum(f["bytes"] for f in files),
            "files": files}
(task / "environment/source_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
print(len(files), "files", manifest["total_bytes"], "bytes")
