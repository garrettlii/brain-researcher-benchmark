"""Write environment/source_manifest.json from the Step-0 download manifest (run from the task directory).

    python -I step0/make_source_manifest.py
"""
import csv
import json
from pathlib import Path

rows = list(csv.DictReader(open("step0/outputs/capslpdb_manifest.tsv"), delimiter="\t"))
files = [{"path": r["rel"], "url": r["url"], "bytes": int(r["bytes"]), "sha256": r["sha256"]} for r in sorted(rows, key=lambda r: r["rel"])]
Path("environment/source_manifest.json").write_text(json.dumps({
    "dataset_id": "PhysioNet CAP Sleep Database 1.0.0 (capslpdb), healthy recordings n1-n16",
    "source": "https://physionet-open.s3.amazonaws.com/capslpdb/1.0.0/ (PhysioNet's public AWS mirror of https://physionet.org/content/capslpdb/1.0.0/)",
    "license": "Open Data Commons Attribution License v1.0",
    "captured": "2026-10-09",
    "n_files": len(files), "total_bytes": sum(f["bytes"] for f in files), "files": files}, indent=1) + "\n")
print(len(files), "files", sum(f["bytes"] for f in files), "bytes")
