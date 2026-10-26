#!/usr/bin/env python3
"""split_gamevideos.py -- build GameVideo rows from the games CSV.

WARNING / README (this is the thing the TA-style advice got wrong):
  The advice said "the data is still sitting in the last column `Movies`".
  That is NOT true for this dataset. Verified against the actual files:

    * games.csv              -> Movies column (data index 39): 0 non-empty rows
    * games_short_clean.csv  -> Movies column (data index 39): 0 non-empty rows

  The `Movies` column is empty everywhere. A `split_videos.py` that reads
  `Movies` would emit 0 rows and GameVideo would stay at 0.

  What actually has data is the `Screenshots` column (data index 38):
    32,356 of the 34,000 short games have screenshot URLs,
    expanding to ~282,000 individual screenshot rows.

  So this script splits `Screenshots`, not `Movies`. The row type is
  'screenshot', which matches the enum we already use locally:
  ENUM('trailer','gameplay','screenshot').

Input  : games_short_clean.csv (no argument) or pass another games CSV.
Output : game_videos.csv next to the input, plus we also write
         /tmp/game_videos.csv so LOAD DATA can read it directly.

Columns written (all quoted, like split_games.py):
  app_id, name, url, video_type
"""

import csv
import sys
from pathlib import Path

csv.field_size_limit(100_000_000)

DEFAULT_NAME = "games_short_clean.csv"


def find_source():
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).expanduser().resolve()
    for folder in (Path.cwd(), Path(__file__).resolve().parent):
        candidate = folder / DEFAULT_NAME
        if candidate.is_file():
            return candidate
    return Path.cwd() / DEFAULT_NAME


def screenshot_index(row_count):
    """Data rows in this CSV have 40 fields while the header only has 39
    (the 'DiscountDLC count' label is one header cell, but the data has two
    cells: Discount and DLC count). So the data is shifted by one relative
    to the header from that point on.

       header label 'Screenshots'  -> index 37
       data value  Screenshots     -> index 38
       header label 'Movies'       -> index 38
       data value  Movies          -> index 39 (empty in this dataset)
    """
    return row_count - 2  # last-but-one data column = Screenshots


def main():
    source = find_source()
    if not source.is_file():
        raise SystemExit(f"{source} not found. Run clean_csvs.py + shorten_csvs.py first.")

    rows = []
    games_with_screenshots = 0
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader)  # header
        for row in reader:
            idx = screenshot_index(len(row))
            app_id = row[0]
            screenshots = row[idx] if idx < len(row) else ""
            if not screenshots.strip():
                continue
            games_with_screenshots += 1
            for i, url in enumerate(screenshots.split(",")):
                url = url.strip()
                if not url:
                    continue
                # Match the naming the DB already uses for screenshots:
                #   "Screenshot 0", "Screenshot 1", ...
                rows.append((app_id, f"Screenshot {i}"[:255], url[:255], "screenshot"))

    out = source.parent / "game_videos.csv"
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writerow(("app_id", "name", "url", "video_type"))
        writer.writerows(rows)

    # Also copy to /tmp so LOAD DATA LOCAL INFILE '/tmp/game_videos.csv' works.
    tmp = Path("/tmp/game_videos.csv")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writerow(("app_id", "name", "url", "video_type"))
        writer.writerows(rows)

    print(f"read {source.name}")
    print(f"games with screenshots: {games_with_screenshots:,}")
    print(f"GameVideo rows written : {len(rows):,}")
    print(f"wrote {out}")
    print(f"wrote {tmp}")


if __name__ == "__main__":
    main()