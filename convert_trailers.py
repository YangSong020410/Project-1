#!/usr/bin/env python3
"""Convert the gold trailers.csv into a GameVideo-loadable CSV.

Usage (from the repo folder):

    python3 convert_trailers.py
    python3 convert_trailers.py /tmp/gold_tier_x/games.csv /tmp/gold_tier_x/trailers.csv

Reads:
  - games.csv from the gold dataset: needs a game_id column and a Steam
    app id column (steam_appid, appid, app_id or steam_app_id).
  - trailers.csv: game_id,trailer_id,name,thumbnail_url,webm_url,mp4_url.

Writes trailer_videos.csv next to this script:
  app_id,name,url,video_type  (video_type is always 'trailer').

Rules:
  - url is the thumbnail_url: webm_url and mp4_url are empty in this file.
  - game_000002 is excluded: its 3 rows are named PAYDAY / F2P Launch,
    but the games table maps game_000002 to PUBG, and PAYDAY 2 already
    has its own rows under game_000027.
  - rows with no url or no game mapping are dropped.
  - dedup on (app_id, url), first row wins.
  - name and url are cut to 255 characters (VARCHAR(255)).
  - every field is quoted, so LOAD DATA uses ENCLOSED BY '"'.

Prints counts at the end; compare them with the reference build
(41,615 rows, 22,013 distinct apps) before loading.
"""

import csv
import sys
from pathlib import Path

csv.field_size_limit(100_000_000)

EXCLUDE_GAMES = {"game_000002"}
APPID_COLUMNS = ("steam_appid", "appid", "app_id", "steam_app_id")


def find_column(fieldnames, wanted, label):
    for name in wanted:
        if name in fieldnames:
            return name
    raise SystemExit(f"{label}: none of {wanted} found in header {fieldnames}")


def main():
    args = sys.argv[1:]
    games_path = Path(args[0]) if len(args) > 0 else Path("/tmp/gold_tier_x/games.csv")
    trailers_path = Path(args[1]) if len(args) > 1 else Path("/tmp/gold_tier_x/trailers.csv")
    out_path = Path(__file__).resolve().parent / "trailer_videos.csv"

    mapping = {}
    with games_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        game_col = find_column(reader.fieldnames, ("game_id",), "games.csv")
        app_col = find_column(reader.fieldnames, APPID_COLUMNS, "games.csv")
        for row in reader:
            app_id = (row[app_col] or "").strip()
            if app_id:
                mapping[(row[game_col] or "").strip()] = app_id
    print(f"games mapped: {len(mapping):,}")

    seen = set()
    out = []
    total = excluded = unmapped = no_url = dups = 0
    with trailers_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total += 1
            game_id = (row["game_id"] or "").strip()
            if game_id in EXCLUDE_GAMES:
                excluded += 1
                continue
            app_id = mapping.get(game_id)
            if app_id is None:
                unmapped += 1
                continue
            url = (row.get("thumbnail_url") or "").strip()[:255]
            if not url:
                no_url += 1
                continue
            key = (app_id, url)
            if key in seen:
                dups += 1
                continue
            seen.add(key)
            name = (row.get("name") or "").strip()[:255]
            out.append((app_id, name, url, "trailer"))

    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writerow(("app_id", "name", "url", "video_type"))
        writer.writerows(out)

    apps = {row[0] for row in out}
    print(f"trailer rows in: {total:,}")
    print(f"excluded (game_000002): {excluded}")
    print(f"dropped, no game mapping: {unmapped}")
    print(f"dropped, no url: {no_url}")
    print(f"dropped, duplicate (app_id, url): {dups}")
    print(f"wrote {out_path.name}: {len(out):,} rows, {len(apps):,} distinct apps")


if __name__ == "__main__":
    main()
