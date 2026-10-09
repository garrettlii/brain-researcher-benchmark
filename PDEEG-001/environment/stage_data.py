"""Build-time staging of the fixed ds002778 files listed in source_manifest.json.

Every file is downloaded from the public OpenNeuro bucket, checked against its recorded size
and sha256, and written under the destination with its BIDS-relative path. Any mismatch or
failed download stops the build: there is no fallback source.

    python3 stage_data.py --manifest source_manifest.json --destination /app/data/ds002778
"""
import argparse
import hashlib
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def fetch(entry, dest):
    target = dest / entry["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    err = "not attempted"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(entry["url"], timeout=300) as r:
                data = r.read()
            if len(data) != entry["bytes"]:
                err = f"size {len(data)} != {entry['bytes']}"
            elif hashlib.sha256(data).hexdigest() != entry["sha256"]:
                err = "sha256 mismatch"
            else:
                target.write_bytes(data)
                return entry["path"], None
        except Exception as e:  # noqa: BLE001
            err = repr(e)
        time.sleep(2 ** attempt)
    return entry["path"], err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--destination", required=True)
    a = ap.parse_args()
    manifest = json.loads(Path(a.manifest).read_text())
    dest = Path(a.destination)
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda e: fetch(e, dest), manifest["files"]))
    bad = [(p, e) for p, e in res if e]
    if bad:
        sys.exit(f"staging failed for {len(bad)} file(s): {bad}")
    print(f"staged {len(res)} files ({manifest['total_bytes']} bytes) into {dest}")


if __name__ == "__main__":
    main()
