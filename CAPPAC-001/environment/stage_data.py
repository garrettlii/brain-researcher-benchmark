"""Build-time staging of the fixed CAP Sleep Database files listed in source_manifest.json.

Every file is streamed from PhysioNet's public AWS mirror, checked against its recorded size
and sha256 (the release's own SHA256SUMS.txt values), and written under the destination. Any
mismatch or failed download stops the build: there is no fallback source.

    python3 stage_data.py --manifest source_manifest.json --destination /app/data/capslpdb
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
    tmp = target.with_name(target.name + ".part")
    err = "not attempted"
    for attempt in range(4):
        try:
            h, n = hashlib.sha256(), 0
            with urllib.request.urlopen(entry["url"], timeout=300) as r, open(tmp, "wb") as f:
                while chunk := r.read(1 << 22):
                    h.update(chunk)
                    n += len(chunk)
                    f.write(chunk)
            if n != entry["bytes"]:
                err = f"size {n} != {entry['bytes']}"
            elif h.hexdigest() != entry["sha256"]:
                err = "sha256 mismatch"
            else:
                tmp.rename(target)
                return entry["path"], None
        except Exception as e:  # noqa: BLE001
            err = repr(e)
        time.sleep(2 ** attempt)
    tmp.unlink(missing_ok=True)
    return entry["path"], err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--destination", required=True)
    a = ap.parse_args()
    manifest = json.loads(Path(a.manifest).read_text())
    dest = Path(a.destination)
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda e: fetch(e, dest), manifest["files"]))
    bad = [(p, e) for p, e in res if e]
    if bad:
        sys.exit(f"staging failed for {len(bad)} file(s): {bad}")
    print(f"staged {len(res)} files ({manifest['total_bytes']} bytes) into {dest}")


if __name__ == "__main__":
    main()
