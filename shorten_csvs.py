#!/usr/bin/env python3
"""Shorten the cleaned NextQuest CSVs to 34,000 rows each.

Put the cleaned files in this folder and run:

    python3 shorten_csvs.py

Reads games_clean.csv, all_reviews_clean.csv, and recommendations_clean.csv.
Writes games_short_clean.csv, all_reviews_short_clean.csv, and
recommendations_short_clean.csv.

The short files match the ones already in data-short-clean:

- Keep the first 34,000 reviews whose app id is in the games file and whose
  review id has not already been kept. Do the same for recommendations,
  using the recommendation id.
- Put every game those rows mention into the short games file, in the
  original games order. Fill the rest of the 34,000 games from the games
  file, still in that order.
- Drop a review or recommendation whose game did not fit in those 34,000.

If the cleaned files are missing, or the first row is not in the cleaned
form, the script asks whether to run clean_csvs.py. Answering no exits.
"""

import csv
import subprocess
import sys
import time
from pathlib import Path

import clean_csvs

csv.field_size_limit(100_000_000)

TARGET = 34_000
CLEAN_NAMES = ("games_clean.csv", "all_reviews_clean.csv", "recommendations_clean.csv")
SHORT_NAMES = {
    "games_clean.csv": "games_short_clean.csv",
    "all_reviews_clean.csv": "all_reviews_short_clean.csv",
    "recommendations_clean.csv": "recommendations_short_clean.csv",
}


class ProgressBar:
    """Progress on stderr. A tty redraws one line; a log gets a line every 2%."""

    def __init__(self, label, total):
        self.label = label
        self.total = max(int(total), 1)
        self.tty = sys.stderr.isatty()
        self.last_draw = 0.0
        self.last_bucket = -1

    def update(self, current, detail=""):
        frac = min(1.0, current / self.total)
        now = time.monotonic()
        bucket = int(frac * 50)
        if self.tty:
            if now - self.last_draw < 0.1 and frac < 1:
                return
        elif bucket == self.last_bucket and frac < 1:
            return
        self.last_draw = now
        self.last_bucket = bucket
        self._draw(frac, detail, end="\r" if self.tty else "\n")

    def close(self):
        if self.tty:
            print("\r" + " " * 110 + "\r", end="", file=sys.stderr, flush=True)

    def _draw(self, frac, detail, end):
        width = 30
        filled = int(width * frac)
        bar = "#" * filled + "-" * (width - filled)
        text = f"{self.label} [{bar}] {frac * 100:5.1f}% {detail}"
        prefix = "\r" if self.tty else ""
        print(f"{prefix}{text[:108]}", end=end, file=sys.stderr, flush=True)


def byte_pos(handle):
    buffer = getattr(handle, "buffer", None)
    if buffer is not None:
        return buffer.tell()
    return 0


def find_folder():
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).expanduser().resolve()
    cwd = Path.cwd()
    here = Path(__file__).resolve().parent
    for folder in (cwd, here):
        if any((folder / name).is_file() for name in CLEAN_NAMES + clean_csvs.SOURCES):
            return folder
    return cwd


def read_record(handle):
    parts = []
    quotes = 0
    while True:
        line = handle.readline()
        if not line:
            return None
        parts.append(line)
        quotes += line.count('"')
        if quotes % 2 == 0:
            return "".join(parts)


def first_data_row(path):
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        if read_record(handle) is None:
            return None
        raw = read_record(handle)
    if raw is None:
        return None
    return next(csv.reader([raw]))


def cleaned_problem(folder):
    missing = [name for name in CLEAN_NAMES if not (folder / name).is_file()]
    if missing:
        return "Missing cleaned files: " + ", ".join(missing)

    games = first_data_row(folder / "games_clean.csv")
    if games is None or clean_csvs.game_row_bad(games, set()) is not None:
        return "games_clean.csv is not in the cleaned form."

    review = first_data_row(folder / "all_reviews_clean.csv")
    if review is None or len(review) != 24 or not clean_csvs.is_int(review[1], 0, clean_csvs.INT_MAX):
        return "all_reviews_clean.csv is not in the cleaned form."
    if clean_csvs.review_row_bad(review, {int(review[1])}, _AcceptIds()) is not None:
        return "all_reviews_clean.csv still has a row the cleaner would drop."

    recommendation = first_data_row(folder / "recommendations_clean.csv")
    if (
        recommendation is None
        or len(recommendation) != 8
        or not clean_csvs.is_int(recommendation[0], 0, clean_csvs.INT_MAX)
    ):
        return "recommendations_clean.csv is not in the cleaned form."
    if (
        clean_csvs.recommendation_row_bad(recommendation, {int(recommendation[0])}, _AcceptIds())
        is not None
    ):
        return "recommendations_clean.csv still has a row the cleaner would drop."
    return None


class _AcceptIds:
    def add_if_new(self, number):
        return 0 <= number <= clean_csvs.INT_MAX


def ask_to_clean(folder, problem):
    print(problem)
    print(f"Folder: {folder}")
    answer = input("Run clean_csvs.py now? [y/n] ").strip().lower()
    if answer not in {"y", "yes"}:
        print("Exiting.")
        raise SystemExit(1)
    script = Path(__file__).resolve().parent / "clean_csvs.py"
    completed = subprocess.run([sys.executable, str(script), str(folder)], check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    problem = cleaned_problem(folder)
    if problem:
        raise SystemExit(problem)


def load_games(path):
    games = []
    bar = ProgressBar("games_clean.csv", path.stat().st_size)
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        header = read_record(handle)
        if header is None:
            bar.close()
            raise SystemExit(f"{path.name} is empty")
        seen = 0
        while True:
            raw = read_record(handle)
            if raw is None:
                break
            seen += 1
            row = next(csv.reader([raw]))
            if row and row[0]:
                games.append((row[0], raw))
            if seen % 2000 == 0:
                bar.update(byte_pos(handle), f"{len(games):,} games")
        bar.update(path.stat().st_size, f"{len(games):,} games")
    bar.close()
    print(f"loaded {len(games):,} games", flush=True)
    return header, games


def take_rows(path, index, id_index, game_ids):
    kept = []
    seen_ids = set()
    apps = set()
    scanned = 0
    bar = ProgressBar(path.name, TARGET)
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        header = read_record(handle)
        if header is None:
            bar.close()
            raise SystemExit(f"{path.name} is empty")
        while len(kept) < TARGET:
            raw = read_record(handle)
            if raw is None:
                break
            scanned += 1
            row = next(csv.reader([raw]))
            if len(row) <= max(index, id_index):
                continue
            app_id = row[index]
            identity = row[id_index]
            if app_id not in game_ids or identity in seen_ids:
                continue
            seen_ids.add(identity)
            kept.append(raw)
            apps.add(app_id)
            if len(kept) % 500 == 0:
                bar.update(len(kept), f"{len(kept):,} / {TARGET:,}")
        if len(kept) != TARGET:
            bar.update(TARGET, f"{len(kept):,} / {TARGET:,}")
    bar.close()
    print(f"{path.name} kept {len(kept):,} scanned {scanned:,}", flush=True)
    return header, kept, apps


def write_rows(folder, source_name, header, rows):
    dest = folder / SHORT_NAMES[source_name]
    temp = dest.with_suffix(dest.suffix + ".shortening")
    with temp.open("w", encoding="utf-8", newline="", buffering=8 * 1024 * 1024) as out:
        out.write(header)
        out.writelines(rows)
    temp.replace(dest)
    print(f"wrote {dest.name} rows {len(rows):,}", flush=True)


def shorten(folder):
    game_header, games = load_games(folder / "games_clean.csv")
    game_ids = {app_id for app_id, _ in games}

    review_header, reviews, review_apps = take_rows(
        folder / "all_reviews_clean.csv", 1, 0, game_ids
    )
    rec_header, recs, rec_apps = take_rows(
        folder / "recommendations_clean.csv", 0, 7, game_ids
    )

    needed = review_apps | rec_apps
    selected = []
    selected_ids = set()
    for app_id, raw in games:
        if app_id in needed and app_id not in selected_ids:
            selected.append((app_id, raw))
            selected_ids.add(app_id)
    for app_id, raw in games:
        if len(selected) >= TARGET:
            break
        if app_id not in selected_ids:
            selected.append((app_id, raw))
            selected_ids.add(app_id)
    selected = selected[:TARGET]
    selected_ids = {app_id for app_id, _ in selected}

    reviews = [raw for raw in reviews if next(csv.reader([raw]))[1] in selected_ids]
    recs = [raw for raw in recs if next(csv.reader([raw]))[0] in selected_ids]

    write_rows(folder, "games_clean.csv", game_header, [raw for _, raw in selected])
    write_rows(folder, "all_reviews_clean.csv", review_header, reviews)
    write_rows(folder, "recommendations_clean.csv", rec_header, recs)


def main():
    folder = find_folder()
    if not folder.is_dir():
        raise SystemExit(f"Folder not found: {folder}")
    print(f"shortening CSVs in {folder}", flush=True)
    problem = cleaned_problem(folder)
    if problem:
        ask_to_clean(folder, problem)
    shorten(folder)


if __name__ == "__main__":
    main()
