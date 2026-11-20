"""Configure the Power BI project to load the downloaded BTS data."""
import argparse
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "Airline Performance Intelligence"
PROJECT = ROOT / "power-bi" / (NAME + ".pbip")
EXPRESSIONS = ROOT / "power-bi" / (NAME + ".SemanticModel") / "definition" / "expressions.tmdl"
PARAMETER = re.compile(r'(?m)^(expression pRawFolder =\n\t\t)"(?:[^"\n]|"")*"( meta \[.*\])$')
MONTHS = ("2024-01", "2024-02", "2025-01", "2025-02")


def set_folder(folder):
    if not PROJECT.is_file():
        raise FileNotFoundError(PROJECT)
    # In M, backslashes are literal. Escape quotes and the M escape introducer.
    escaped = str(folder).replace("#(", "#(#)(").replace('"', '""')
    source = EXPRESSIONS.read_text(encoding="utf-8")
    configured, matches = PARAMETER.subn(lambda m: m[1] + '"' + escaped + '"' + m[2], source)
    if matches != 1:
        raise ValueError("Expected exactly one pRawFolder parameter in expressions.tmdl.")
    if configured != source:
        with tempfile.TemporaryDirectory(dir=EXPRESSIONS.parent) as temp:
            path = Path(temp) / EXPRESSIONS.name
            path.write_bytes(configured.encode("utf-8"))
            path.replace(EXPRESSIONS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-folder", type=Path, default=ROOT / "data" / "raw",
                        help="Folder containing the four BTS CSVs.")
    parser.add_argument("--launch", action="store_true", help="Open the configured project in Power BI Desktop.")
    args = parser.parse_args()
    if args.launch and os.name != "nt":
        parser.error("--launch requires Windows with Power BI Desktop installed.")
    folder = args.raw_folder.resolve()
    missing = [month for month in MONTHS if not (folder / (month + ".csv")).is_file()]
    if missing:
        parser.error(f"Missing source CSVs in {folder}: {', '.join(missing)}")
    set_folder(folder)
    print(f"Configured source folder: {folder}")
    print(f"Power BI project: {PROJECT}")
    if args.launch:
        os.startfile(PROJECT)


if __name__ == "__main__":
    main()
