"""Fetch the UNM resting EEG set (PRED+CT accession d002, "Parkinson's Rests", 27 PD / 27 CTL).

PRED+CT (https://predict.cs.unm.edu/downloads.php, Public Domain Dedication and License)
links d002 to http://bit.ly/2rfCkNP, a SharePoint guest-access folder ("PD REST"). The folder
also holds unrelated third-party uploads and *_REST1.mat duplicates; only <id>_<session>_PD_REST.mat
and IMPORT_ME_REST.xlsx are fetched, and a sha256 manifest is written next to the outputs.

    python step0/fetch_unm_d002.py <outdir>
"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SHORT = "http://bit.ly/2rfCkNP"
BASE = "https://unmm-my.sharepoint.com/personal/jcavanagh_unm_edu"
FOLDER = "/personal/jcavanagh_unm_edu/Documents/PD REST"
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
cj = Path(tempfile.mkdtemp()) / "cookies"


def curl(*args):
    return subprocess.run(["curl", "-s", "-f", "-L", "-b", str(cj), "-c", str(cj), *args], check=True,
                          capture_output=True).stdout


curl(SHORT, "-o", "/dev/null")                                     # guest-access session cookie
listing = json.loads(curl("-H", "Accept: application/json;odata=nometadata",
                          f"{BASE}/_api/web/GetFolderByServerRelativeUrl('{urllib.parse.quote(FOLDER)}')/Files"))["value"]
want = {f["Name"]: int(f["Length"]) for f in listing
        if re.fullmatch(r"\d+_[12]_PD_REST\.mat", f["Name"]) or f["Name"] == "IMPORT_ME_REST.xlsx"}


def get(name):
    f = out / name
    if not (f.exists() and f.stat().st_size == want[name]):
        url = f"{BASE}/_api/web/GetFileByServerRelativeUrl('{urllib.parse.quote(FOLDER + '/' + name)}')/$value"
        for _ in range(3):
            try:
                curl("--max-time", "600", url, "-o", str(f))
                break
            except subprocess.CalledProcessError:
                continue
    ok = f.exists() and f.stat().st_size == want[name]
    return name, ok, hashlib.sha256(f.read_bytes()).hexdigest() if ok else ""


with ThreadPoolExecutor(8) as ex:
    rows = sorted(ex.map(get, want))
bad = [n for n, ok, _ in rows if not ok]
manifest = Path(__file__).resolve().parent / "outputs" / "unm_d002_sha256.tsv"
manifest.write_text("".join(f"{n}\t{h}\n" for n, ok, h in rows if ok))
print(f"{len(rows) - len(bad)}/{len(rows)} files ok; manifest {manifest}")
if bad:
    sys.exit(f"failed: {bad}")
