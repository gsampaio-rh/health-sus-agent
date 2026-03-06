#!/usr/bin/env python3
"""Download SIA (outpatient) data from DATASUS for São Paulo.

Usage:
    python scripts/download_sia.py

Downloads PA (Produção Ambulatorial) files for SP, 2022-2025.
Each monthly file is ~140MB DBC → ~10MB parquet. Expect ~1-2 min per file.
Total: ~48 files, ~30-90 min depending on connection.

The script is resumable — skips files already downloaded.
"""
import time
from pathlib import Path

from tqdm import tqdm


def main():
    from pysus import SIA

    output_dir = Path("data/sia")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading SIA metadata from DATASUS FTP...")
    sia = SIA().load()

    years = list(range(2023, 2026))
    months = list(range(1, 13))

    # First pass: collect all files to know total count
    all_files = []
    print("Listing files...")
    for year in years:
        for month in months:
            try:
                files = sia.get_files("PA", uf="SP", year=year, month=month)
                for f in files:
                    desc = sia.describe(f)
                    all_files.append((f, desc, year, month))
            except Exception:
                pass

    print(f"Found {len(all_files)} files total.\n")

    total_downloaded = 0
    total_skipped = 0
    total_failed = 0

    pbar = tqdm(all_files, unit="file", desc="Downloading SIA SP")
    for f, desc, year, month in pbar:
        fname = desc.get("name", str(f))
        stem = Path(fname).stem
        target = output_dir / f"{stem}.parquet"

        if target.exists():
            total_skipped += 1
            pbar.set_postfix(dl=total_downloaded, skip=total_skipped, fail=total_failed)
            continue

        pbar.set_description(f"{fname} ({desc.get('size', '?')})")
        t0 = time.time()

        try:
            f.download(local_dir=str(output_dir))
            elapsed = time.time() - t0
            total_downloaded += 1
            pbar.set_postfix(dl=total_downloaded, skip=total_skipped, fail=total_failed, last=f"{elapsed:.0f}s")
        except Exception as e:
            total_failed += 1
            pbar.set_postfix(dl=total_downloaded, skip=total_skipped, fail=total_failed, err=str(e)[:30])

    pbar.close()

    print(f"\nDone. Downloaded: {total_downloaded}, Skipped: {total_skipped}, Failed: {total_failed}")
    parquets = list(output_dir.glob("*.parquet"))
    print(f"Files in {output_dir}: {len(parquets)} parquets")
    if parquets:
        total_size = sum(p.stat().st_size for p in parquets)
        print(f"Total size: {total_size / 1e9:.1f} GB")


if __name__ == "__main__":
    main()
