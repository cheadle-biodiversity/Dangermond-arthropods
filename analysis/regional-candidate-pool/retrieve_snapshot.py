"""Resume the public GBIF DOI archive using checked HTTP byte ranges."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import shutil
import urllib.request
import urllib.error
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "data/raw/gbif/california_2026-09-28"
KEY = "0010070-260921141020460"
FOLDER.mkdir(parents=True, exist_ok=True)
metadata = json.load(urllib.request.urlopen(f"https://api.gbif.org/v1/occurrence/download/{KEY}"))
assert metadata["doi"] == "10.15468/dl.vgv5ee" and metadata["status"] == "SUCCEEDED"
size = metadata["size"]
target = FOLDER / f"{KEY}.zip"
parts = FOLDER / "download_parts"
parts.mkdir(exist_ok=True)
prefix = parts / "prefix"
if target.exists() and target.stat().st_size < size:
    assert not prefix.exists()
    target.rename(prefix)
if target.exists():
    assert target.stat().st_size == size
else:
    start = prefix.stat().st_size if prefix.exists() else 0
    chunks = [(a, min(a + 32 * 1024 * 1024, size) - 1) for a in range(start, size, 32 * 1024 * 1024)]

    def fetch(bounds):
        a, b = bounds
        path = parts / f"{a:012d}-{b:012d}"
        if path.exists() and path.stat().st_size == b - a + 1:
            return path
        request = urllib.request.Request(metadata["downloadLink"], headers={"Range": f"bytes={a}-{b}"})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(request, timeout=120) as response, path.open("wb") as out:
                    assert response.status == 206, "Server must support exact byte ranges"
                    assert response.headers["Content-Range"].startswith(f"bytes {a}-{b}/")
                    shutil.copyfileobj(response, out, length=1024 * 1024)
                break
            except urllib.error.HTTPError as error:
                if error.code != 429 or attempt == 4:
                    raise
                delay = int(error.headers.get("Retry-After", "60"))
                print(f"GBIF rate limit; respecting {delay}-second retry delay.", flush=True)
                while delay:
                    pause = min(delay, 60)
                    time.sleep(pause)
                    delay -= pause
        assert path.stat().st_size == b - a + 1
        return path

    done = start
    # One transfer at a time to respect the GBIF download service's limits.
    with ThreadPoolExecutor(max_workers=1) as pool:
        tasks = {pool.submit(fetch, c): c for c in chunks}
        for task in as_completed(tasks):
            path = task.result()
            done += path.stat().st_size
            print(f"Downloaded {done / 1e6:.1f} / {size / 1e6:.1f} MB", flush=True)
    assembled = target.with_suffix(".zip.partial")
    with assembled.open("wb") as out:
        if prefix.exists():
            with prefix.open("rb") as source:
                shutil.copyfileobj(source, out)
        for a, b in chunks:
            with (parts / f"{a:012d}-{b:012d}").open("rb") as source:
                shutil.copyfileobj(source, out)
    assert assembled.stat().st_size == size
    assembled.replace(target)

with zipfile.ZipFile(target) as archive:
    print("Validating complete ZIP...", flush=True)
    assert archive.testzip() is None
digest = hashlib.file_digest(target.open("rb"), "sha256").hexdigest()
(FOLDER / "download_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
(FOLDER / "archive_manifest.json").write_text(json.dumps({"doi": metadata["doi"], "file": target.name, "bytes": size, "sha256": digest, "retrieved_on": "2026-10-27", "zip_crc_validated": True}, indent=2) + "\n")
(FOLDER / "doi.txt").write_text(metadata["doi"] + "\n")
shutil.rmtree(parts)
print("Archive complete and verified.", flush=True)
