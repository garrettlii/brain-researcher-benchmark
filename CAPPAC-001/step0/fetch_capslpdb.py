"""Download the 16 healthy recordings (n1-n16: EDF + RemLogic event export) of the PhysioNet CAP Sleep
Database 1.0.0 (open, ODC-By 1.0) and check them against PhysioNet's SHA256SUMS.txt.

    python step0/fetch_capslpdb.py <dest> [threads]
"""
import hashlib
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# physionet-open is PhysioNet's public AWS mirror of https://physionet.org/files/capslpdb/1.0.0/ (identical files; much faster)
BASE = "https://physionet-open.s3.amazonaws.com/capslpdb/1.0.0/"
dest = Path(sys.argv[1]).expanduser()
nthreads = int(sys.argv[2]) if len(sys.argv) > 2 else 4
dest.mkdir(parents=True, exist_ok=True)

sums = {}
for line in urllib.request.urlopen(BASE + "SHA256SUMS.txt").read().decode().splitlines():
    h, name = line.split(maxsplit=1)
    sums[name.strip()] = h
files = [f"n{i}.{ext}" for i in range(1, 17) for ext in ("edf", "txt")]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1 << 22):
            h.update(chunk)
    return h.hexdigest()


def get(name):
    out = dest / name
    if not (out.exists() and sha(out) == sums[name]):
        tmp = out.with_suffix(out.suffix + ".part")
        with urllib.request.urlopen(BASE + name) as r, open(tmp, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        tmp.rename(out)
    digest = sha(out)
    assert digest == sums[name], name
    return name, out.stat().st_size, digest, BASE + name


with ThreadPoolExecutor(nthreads) as ex:
    rows = list(ex.map(get, files))
with open(dest / "manifest.tsv", "w") as f:
    f.write("rel\tbytes\tsha256\turl\n")
    for r in sorted(rows):
        f.write("\t".join(map(str, r)) + "\n")
print(len(rows), "files,", sum(r[1] for r in rows), "bytes, all match SHA256SUMS.txt")
