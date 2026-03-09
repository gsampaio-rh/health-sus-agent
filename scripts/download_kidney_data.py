#!/usr/bin/env python3
"""Download all data required for the kidney stone experiment v2.

Usage:
    python scripts/download_kidney_data.py [--skip-cross-state]

Downloads:
    1. SIH RD (SP, 2016-2025)     — hospital admissions        [already downloaded]
    2. CNES ST (SP, 2016-2025)    — facility registry           [already downloaded]
    3. CNES EQ (SP, 2024-2025)    — equipment inventory
    4. CNES LT (SP, 2024-2025)    — bed types
    5. CNES PF (SP, 2024-2025)    — professional staff
    6. SIA PA  (SP, 2022-2025)    — outpatient billing          [already downloaded]
    7. SIH RD  (RJ,MG,BA 2022-25)— cross-state validation
    8. CNES ST (RJ,MG,BA 2024-25)— cross-state facilities

The script is resumable — skips files already on disk.
"""
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.domain.models import DatabaseSource, DownloadRequest
from src.infrastructure.datasus.registry import create_adapter


DOWNLOAD_TASKS = [
    {
        "label": "CNES EQ (SP, equipment)",
        "source": DatabaseSource.CNES,
        "uf": "SP",
        "years": [2024, 2025],
        "group": "EQ",
        "output_subdir": "cnes",
    },
    {
        "label": "CNES LT (SP, beds)",
        "source": DatabaseSource.CNES,
        "uf": "SP",
        "years": [2024, 2025],
        "group": "LT",
        "output_subdir": "cnes",
    },
    {
        "label": "CNES PF (SP, professionals)",
        "source": DatabaseSource.CNES,
        "uf": "SP",
        "years": [2024, 2025],
        "group": "PF",
        "output_subdir": "cnes",
    },
]

CROSS_STATE_TASKS = [
    {
        "label": "SIH RD (RJ, 2022-2025)",
        "source": DatabaseSource.SIH,
        "uf": "RJ",
        "years": [2022, 2023, 2024, 2025],
        "group": "RD",
        "output_subdir": "sih",
    },
    {
        "label": "SIH RD (MG, 2022-2025)",
        "source": DatabaseSource.SIH,
        "uf": "MG",
        "years": [2022, 2023, 2024, 2025],
        "group": "RD",
        "output_subdir": "sih",
    },
    {
        "label": "SIH RD (BA, 2022-2025)",
        "source": DatabaseSource.SIH,
        "uf": "BA",
        "years": [2022, 2023, 2024, 2025],
        "group": "RD",
        "output_subdir": "sih",
    },
    {
        "label": "CNES ST (RJ, 2024-2025)",
        "source": DatabaseSource.CNES,
        "uf": "RJ",
        "years": [2024, 2025],
        "group": "ST",
        "output_subdir": "cnes",
    },
    {
        "label": "CNES ST (MG, 2024-2025)",
        "source": DatabaseSource.CNES,
        "uf": "MG",
        "years": [2024, 2025],
        "group": "ST",
        "output_subdir": "cnes",
    },
    {
        "label": "CNES ST (BA, 2024-2025)",
        "source": DatabaseSource.CNES,
        "uf": "BA",
        "years": [2024, 2025],
        "group": "ST",
        "output_subdir": "cnes",
    },
]


def file_already_exists(output_dir: Path, file_name: str) -> bool:
    stem = Path(file_name).stem
    return (output_dir / f"{stem}.parquet").exists() or (output_dir / file_name).exists()


def download_task(task: dict, data_dir: Path) -> tuple[int, int, int]:
    label = task["label"]
    output_dir = data_dir / task["output_subdir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    adapter = create_adapter(task["source"])

    request = DownloadRequest(
        source=task["source"],
        uf=task["uf"],
        years=task["years"],
        group=task["group"],
    )

    print("  Listing files from DATASUS FTP...")
    files = adapter.list_files(request)
    print(f"  Found {len(files)} files")

    downloaded, skipped, failed = 0, 0, 0

    for meta in files:
        if file_already_exists(output_dir, meta.name):
            skipped += 1
            continue

        print(f"  Downloading {meta.name}...", end=" ", flush=True)
        t0 = time.time()
        result = adapter.download_file(meta, output_dir)

        if result.status.value == "completed":
            elapsed = time.time() - t0
            print(f"OK ({result.rows_count:,} rows, {elapsed:.0f}s)")
            downloaded += 1
        else:
            print(f"FAILED: {result.error_message}")
            failed += 1

    print(f"  Summary: {downloaded} downloaded, {skipped} skipped, {failed} failed")
    return downloaded, skipped, failed


def main():
    skip_cross_state = "--skip-cross-state" in sys.argv
    data_dir = PROJECT_ROOT / "data"

    tasks = list(DOWNLOAD_TASKS)
    if not skip_cross_state:
        tasks.extend(CROSS_STATE_TASKS)
    else:
        print("Skipping cross-state data (--skip-cross-state)")

    total_dl, total_skip, total_fail = 0, 0, 0

    for task in tasks:
        dl, skip, fail = download_task(task, data_dir)
        total_dl += dl
        total_skip += skip
        total_fail += fail

    print(f"\n{'='*60}")
    print(f"  ALL DONE")
    print(f"  Downloaded: {total_dl}  Skipped: {total_skip}  Failed: {total_fail}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
