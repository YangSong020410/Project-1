#!/usr/bin/env python3
"""Fetch Steam store video URLs for trailer rows and write video_links.csv.

Usage (from the repo folder):

    # 1. Export the app ids that actually have trailer rows in your DB:
    mysql -u root -p -N -e "SELECT DISTINCT app_id FROM NextQuest.GameVideo WHERE video_type='trailer' ORDER BY app_id;" > appids.txt

    # 2. Test with one app first (CS2 = 730), then run the full file:
    echo 730 > appids.txt && python3 fetch_steam_videos.py
    python3 fetch_steam_videos.py

App id source: appids.txt next to this script if it exists, otherwise
the distinct app_id values in trailer_videos.csv next to this script.

NOTE: the store.steampowered.com/api/appdetails endpoint no longer accepts
comma-separated lists of appids (it returns HTTP 400 for more than one id),
so we request one appid per call and fan out with a small thread pool.

Output video_links.csv (next to this script):
  app_id,movie_id,name,mp4_url,webm_url
  - one row per movie the Steam store API returns for the app.
  - mp4_url prefers mp4 'max'; if absent (current store API), falls back to
    hls_h264 (HLS master playlist, .m3u8 - plays natively in Safari and via
    hls.js elsewhere).
  - webm_url prefers webm 'max'; if absent, falls back to dash_h264 (DASH
    manifest, .mpd - plays via dash.js).
  - urls are NOT truncated: the script prints the longest url so you can
    confirm everything fits VARCHAR(255) before loading.

Failed app ids (HTTP error after retries, or success=false, e.g. age-gated
or removed games) are written to failed_appids.txt; rerun with that file as
appids.txt to retry just those.

The Steam store API (appdetails) is unofficial and rate-limited, so this is
a one-off batch job. Never call it once per page load from the web app; run
it once and store the results.
"""

import csv
import json
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

WORKERS = 8
PAUSE = 0.15  # seconds between each worker's request, keeps 429s away
API = ("https://store.steampowered.com/api/appdetails"
       "?appids={appid}&cc=us&l=en&filters=movies")
HEADERS = {"User-Agent": "Mozilla/5.0 (NextQuest CS5200 project batch job)"}

_lock = threading.Lock()
_progress = {"done": 0, "rows": 0, "failed": 0}


def load_appids(folder):
    appids_file = folder / "appids.txt"
    if appids_file.is_file():
        ids = [line.strip() for line in appids_file.read_text(encoding="utf-8").splitlines()]
        return [i for i in ids if i]
    csv_file = folder / "trailer_videos.csv"
    if not csv_file.is_file():
        raise SystemExit("Need appids.txt or trailer_videos.csv next to this script.")
    ids = set()
    with csv_file.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("app_id"):
                ids.add(row["app_id"].strip())
    return sorted(ids)


def fetch_one(app_id):
    """Return (app_id, rows, failed) for a single appid."""
    url = API.format(appid=app_id)
    request = urllib.request.Request(url, headers=HEADERS)

    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            entry = data.get(app_id, {}) or {}
            if not entry.get("success"):
                return app_id, [], True

            rows = []
            for movie in (entry.get("data") or {}).get("movies", []):
                # Current store API returns hls_h264 / dash_h264 / dash_av1
                # instead of the old mp4/webm max URLs. Keep the two-column
                # CSV shape the backfill SQL expects, and fall back to the
                # HLS/DASH manifests so video_url still gets a playable link.
                mp4 = (movie.get("mp4") or {}).get("max", "") or movie.get("hls_h264", "")
                webm = (movie.get("webm") or {}).get("max", "") or movie.get("dash_h264", "")
                rows.append((app_id, str(movie.get("id", "")),
                             (movie.get("name") or "")[:255], mp4, webm))
            return app_id, rows, False
        except urllib.error.HTTPError as error:
            # 429/5xx retry; anything else (400/403/404/410) is permanent.
            if error.code not in (429, 500, 502, 503, 504):
                return app_id, [], True
            wait = 5 * (attempt + 1) if error.code == 429 else 2 * (attempt + 1)
            time.sleep(wait)
        except Exception:
            time.sleep(2 * (attempt + 1))

    return app_id, [], True


def main():
    folder = Path(__file__).resolve().parent
    appids = load_appids(folder)
    print(f"apps to fetch: {len(appids):,}", flush=True)

    all_rows = []
    failed = []

    def run(app_id):
        time.sleep(PAUSE)
        app_id, rows, is_failed = fetch_one(app_id)
        with _lock:
            _progress["done"] += 1
            if is_failed:
                failed.append(app_id)
                _progress["failed"] += 1
            else:
                all_rows.extend(rows)
                _progress["rows"] += len(rows)
            done = _progress["done"]
            if done % 100 == 0 or done == len(appids):
                print(f"  {done}/{len(appids)} apps done, "
                      f"{_progress['rows']:,} movies, "
                      f"{_progress['failed']:,} failed", flush=True)
        return app_id, rows, is_failed

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(run, app_id) for app_id in appids]
        for _ in as_completed(futures):
            pass

    # Sort rows deterministically by (app_id, movie_id) for stable diffs.
    all_rows.sort(key=lambda r: (int(r[0]), r[1]))

    max_url = max((len(r[3]) for r in all_rows if r[3]), default=0)
    max_url = max(max_url, max((len(r[4]) for r in all_rows if r[4]), default=0))

    out_path = folder / "video_links.csv"
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writerow(("app_id", "movie_id", "name", "mp4_url", "webm_url"))
        writer.writerows(all_rows)

    failed_path = folder / "failed_appids.txt"
    failed_path.write_text("\n".join(str(a) for a in failed) + ("\n" if failed else ""),
                           encoding="utf-8")

    print(f"wrote {out_path.name}: {len(all_rows):,} movies", flush=True)
    print(f"failed apps: {len(failed)} (see {failed_path.name})", flush=True)
    print(f"longest video url: {max_url} chars (must be <= 255)", flush=True)
    if not all_rows:
        print("WARNING: zero movies fetched. If the API ignored the filters "
              "parameter, remove '&filters=movies' from API and rerun.", flush=True)


if __name__ == "__main__":
    main()