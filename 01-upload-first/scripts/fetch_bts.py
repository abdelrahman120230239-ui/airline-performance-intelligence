"""Fetch the pinned BTS archives and extract their main CSVs (Python 3.11+)."""
import argparse
import csv
import hashlib
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]

def fetch(row, destination, archive_dir, accept_revision):
    archive = archive_dir / row["url"].rsplit("/", 1)[-1]
    if not archive.is_file():
        partial = archive.with_suffix(".part")
        try:
            request = Request(row["url"], headers={"User-Agent": "AirlinePerformanceIntelligence/1.0"})
            with urlopen(request, timeout=120) as response, partial.open("wb") as stream:
                shutil.copyfileobj(response, stream)
            partial.replace(archive)
        finally:
            partial.unlink(missing_ok=True)
    with archive.open("rb") as stream:
        actual_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual_hash != row["sha256"] and not accept_revision:
        raise ValueError(f"{row['month']}: SHA-256 changed ({actual_hash}). Review source revision.")
    target = destination / (row["month"] + ".csv")
    partial = target.with_suffix(".part")
    try:
        with ZipFile(archive) as bundle:
            members = [member for member in bundle.namelist()
                       if Path(member).name.lower().startswith("on_time_")
                       and member.lower().endswith(".csv")]
            if len(members) != 1:
                raise ValueError(f"Expected one flight CSV in {archive.name}. Found {members}")
            with bundle.open(members[0]) as source, partial.open("wb") as sink:
                shutil.copyfileobj(source, sink)
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    print(f"Extracted {target} ({target.stat().st_size:,} bytes, SHA-256 {actual_hash})")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--archives", type=Path, help="Optional directory for caching ZIPs")
    parser.add_argument("--accept-revision", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with (ROOT / "docs" / "source-manifest.csv").open(newline="", encoding="utf-8") as manifest:
        rows = list(csv.DictReader(manifest))
    with tempfile.TemporaryDirectory() as temporary:
        archives = args.archives or Path(temporary)
        archives.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda row: fetch(row, args.out, archives, args.accept_revision), rows))

if __name__ == "__main__":
    main()
