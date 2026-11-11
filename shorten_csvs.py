#!/usr/bin/env python3
# Run this file with python3. It cuts the cleaned files down to 34,000 rows each.

"""Shorten the cleaned files to 34,000 rows each.

Put the cleaned files in this folder and run:

    python3 shorten_csvs.py

Reads games_clean.csv, all_reviews_clean.csv, and recommendations_clean.csv.
Writes games_short_clean.csv, all_reviews_short_clean.csv, and
recommendations_short_clean.csv.

Keep the first 34,000 reviews whose app_id is in the games file and whose
review id has not already been kept. Do the same for recommendations, using
the recommendation id.

Put every game those rows mention into the short games file, in the original
games order. Fill the rest of the 34,000 games from the games file, still in
that order.

Drop a review or recommendation whose game did not fit in those 34,000.

If a cleaned file is missing, or the first data row is not in cleaned form,
this asks whether to run clean_csvs.py. Answering no stops.
"""

# csv splits one record into fields.
import csv
# subprocess starts clean_csvs.py when the cleaned files are not ready.
import subprocess
# sys holds the typed folder name, and the python program used to start the cleaner.
import sys
# time supplies a clock for the progress line.
import time
# Path is a file location.
from pathlib import Path

# clean_csvs has the same row checks used before LOAD DATA INFILE.
import clean_csvs

# A single field may be very long. Raise the limit so a long description is not rejected.
csv.field_size_limit(100_000_000)

# How many data rows each short file should hold.
TARGET = 34_000
# The three cleaned names this script reads.
CLEAN_NAMES = ("games_clean.csv", "all_reviews_clean.csv", "recommendations_clean.csv")
# Each cleaned name maps to the short file written from it.
SHORT_NAMES = {
    "games_clean.csv": "games_short_clean.csv",
    "all_reviews_clean.csv": "all_reviews_short_clean.csv",
    "recommendations_clean.csv": "recommendations_short_clean.csv",
}


# Draw a progress line while rows are read or chosen.
# label is text, the name printed on the line.
# total is an int, how much work the line represents.
# Nothing is returned.
class ProgressBar:
    # Save the name and the total on this bar.
    # label is text. total is an int. Nothing is returned.
    def __init__(self, label, total):
        self.label = label
        # Use at least 1 so a later division never divides by zero.
        self.total = max(int(total), 1)
        # True when messages go to a screen you are watching.
        self.tty = sys.stderr.isatty()
        # Clock time of the previous redraw. 0.0 means none yet.
        self.last_draw = 0.0
        # Last progress step printed. -1 means none yet.
        self.last_bucket = -1

    # Reprint the line when enough time, or enough progress, has passed.
    # current is an int. detail is extra text. Nothing is returned.
    def update(self, current, detail=""):
        # Share finished, held between 0 and 1.
        frac = min(1.0, current / self.total)
        now = time.monotonic()
        # Cut that share into 50 steps.
        bucket = int(frac * 50)
        # On a live screen, skip a redraw that comes too soon.
        if self.tty:
            if now - self.last_draw < 0.1 and frac < 1:
                return
        # In a log, print again only when the step changes.
        elif bucket == self.last_bucket and frac < 1:
            return
        self.last_draw = now
        self.last_bucket = bucket
        # A live screen rewrites one line. A log starts a new line.
        self._draw(frac, detail, end="\r" if self.tty else "\n")

    # Wipe the progress line off a live screen. Nothing is returned.
    def close(self):
        if self.tty:
            print("\r" + " " * 110 + "\r", end="", file=sys.stderr, flush=True)

    # Print one progress line.
    # frac is the share finished. detail is extra text. end closes the line.
    # Nothing is returned.
    def _draw(self, frac, detail, end):
        width = 30
        filled = int(width * frac)
        # # is finished. - is still left.
        bar = "#" * filled + "-" * (width - filled)
        text = f"{self.label} [{bar}] {frac * 100:5.1f}% {detail}"
        prefix = "\r" if self.tty else ""
        # Keep the line short, print it with the error messages, and push it out now.
        print(f"{prefix}{text[:108]}", end=end, file=sys.stderr, flush=True)


# Return how many bytes have been read, as an int.
# handle is the open file.
def byte_pos(handle):
    buffer = getattr(handle, "buffer", None)
    if buffer is not None:
        return buffer.tell()
    return 0


# Return the folder to read, as a Path.
# A folder typed after the script name wins. Otherwise use the folder you ran from, then this file's folder.
def find_folder():
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).expanduser().resolve()
    cwd = Path.cwd()
    here = Path(__file__).resolve().parent
    # Use the first of those two folders that already has a cleaned file or a raw source file.
    for folder in (cwd, here):
        if any((folder / name).is_file() for name in CLEAN_NAMES + clean_csvs.SOURCES):
            return folder
    return cwd


# Read one csv record. A quoted field that spans lines stays one record.
# handle is the open file. Return the record text, or None at the end of the file.
def read_record(handle):
    parts = []
    # An even quote count means the record is closed.
    quotes = 0
    while True:
        line = handle.readline()
        if not line:
            return None
        parts.append(line)
        quotes += line.count('"')
        if quotes % 2 == 0:
            return "".join(parts)


# Return the first data row as a list of text fields, or None if the file has no data row.
# path is a Path.
def first_data_row(path):
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        # Skip the header, the column-name line.
        if read_record(handle) is None:
            return None
        raw = read_record(handle)
    if raw is None:
        return None
    # Split that one record into fields.
    return next(csv.reader([raw]))


# Return None when the three cleaned files look usable. Otherwise return text saying what is wrong.
# folder is a Path.
def cleaned_problem(folder):
    # A missing cleaned file has to be built by clean_csvs.py first.
    missing = [name for name in CLEAN_NAMES if not (folder / name).is_file()]
    if missing:
        return "Missing cleaned files: " + ", ".join(missing)

    # The first game row must pass the same checks clean_csvs uses. The empty set stands in for ids already seen.
    games = first_data_row(folder / "games_clean.csv")
    if games is None or clean_csvs.game_row_bad(games, set()) is not None:
        return "games_clean.csv is not in the cleaned form."

    # The first review row must have 24 fields and an INT app_id.
    review = first_data_row(folder / "all_reviews_clean.csv")
    if review is None or len(review) != 24 or not clean_csvs.is_int(review[1], 0, clean_csvs.INT_MAX):
        return "all_reviews_clean.csv is not in the cleaned form."
    # Pretend that app_id is a kept game, and pretend no review id has been seen yet.
    if clean_csvs.review_row_bad(review, {int(review[1])}, _AcceptIds()) is not None:
        return "all_reviews_clean.csv still has a row the cleaner would drop."

    # The first recommendation row must have 8 fields and an INT app_id.
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


# A stand-in id set for the first-row check. It does not remember ids.
class _AcceptIds:
    # Return True when number fits in an INT from 0 up. The id is not stored.
    # number is an int.
    def add_if_new(self, number):
        return 0 <= number <= clean_csvs.INT_MAX


# Ask whether to run clean_csvs.py, then run it if the answer is yes.
# folder is a Path. problem is text, what is wrong with the cleaned files.
# Nothing is returned. A no answer, or a failed clean, stops the script.
def ask_to_clean(folder, problem):
    print(problem)
    print(f"Folder: {folder}")
    # Wait for a typed answer. Strip spaces and ignore capital letters.
    answer = input("Run clean_csvs.py now? [y/n] ").strip().lower()
    if answer not in {"y", "yes"}:
        print("Exiting.")
        raise SystemExit(1)
    # This file's folder holds clean_csvs.py.
    script = Path(__file__).resolve().parent / "clean_csvs.py"
    # Start that script with the same python, on this folder, and wait until it finishes.
    completed = subprocess.run([sys.executable, str(script), str(folder)], check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    # Check the cleaned files again after the cleaner finishes.
    problem = cleaned_problem(folder)
    if problem:
        raise SystemExit(problem)


# Read every game row.
# path is a Path, the cleaned games file.
# Return the header text, and a list of pairs. Each pair is (app_id text, original row text).
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
            # Keep the app_id text and the original row. Skip a row with an empty first field.
            if row and row[0]:
                games.append((row[0], raw))
            # Refresh the line every 2,000 records.
            if seen % 2000 == 0:
                bar.update(byte_pos(handle), f"{len(games):,} games")
        bar.update(path.stat().st_size, f"{len(games):,} games")
    bar.close()
    print(f"loaded {len(games):,} games", flush=True)
    return header, games


# Keep the first TARGET rows whose game was kept and whose own id is new.
# path is a Path. index is an int, the field that holds app_id.
# id_index is an int, the field that holds this row's own id.
# game_ids is a set of app_id text from the games file.
# Return the header text, the list of kept row texts, and the set of app_id text those rows name.
def take_rows(path, index, id_index, game_ids):
    kept = []
    # seen_ids holds ids already kept, so a repeat is skipped.
    seen_ids = set()
    # apps holds the app_id values the kept rows name.
    apps = set()
    scanned = 0
    bar = ProgressBar(path.name, TARGET)
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        header = read_record(handle)
        if header is None:
            bar.close()
            raise SystemExit(f"{path.name} is empty")
        # Stop once TARGET rows are kept, or the file ends.
        while len(kept) < TARGET:
            raw = read_record(handle)
            if raw is None:
                break
            scanned += 1
            row = next(csv.reader([raw]))
            # A short row does not have the app_id field and the id field. Skip it.
            if len(row) <= max(index, id_index):
                continue
            app_id = row[index]
            identity = row[id_index]
            # Skip a game that was not kept, and skip an id already kept.
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


# Write the header and the chosen rows to the short file.
# folder is a Path. source_name is text, a cleaned file name.
# header is text. rows is a list of row texts.
# Nothing is returned.
def write_rows(folder, source_name, header, rows):
    dest = folder / SHORT_NAMES[source_name]
    # Write a side file, then swap it into the short name when the write finishes.
    temp = dest.with_suffix(dest.suffix + ".shortening")
    with temp.open("w", encoding="utf-8", newline="", buffering=8 * 1024 * 1024) as out:
        out.write(header)
        out.writelines(rows)
    temp.replace(dest)
    print(f"wrote {dest.name} rows {len(rows):,}", flush=True)


# Build the three short files from the cleaned files.
# folder is a Path. Nothing is returned.
def shorten(folder):
    game_header, games = load_games(folder / "games_clean.csv")
    # game_ids is every app_id text in the cleaned games file.
    game_ids = {app_id for app_id, _ in games}

    # Reviews: app_id is field 1, review id is field 0.
    review_header, reviews, review_apps = take_rows(
        folder / "all_reviews_clean.csv", 1, 0, game_ids
    )
    # Recommendations: app_id is field 0, recommendation id is field 7.
    rec_header, recs, rec_apps = take_rows(
        folder / "recommendations_clean.csv", 0, 7, game_ids
    )

    # needed is every app_id the kept reviews or recommendations mention.
    needed = review_apps | rec_apps
    selected = []
    selected_ids = set()
    # First pass: take those needed games, in the original games order.
    for app_id, raw in games:
        if app_id in needed and app_id not in selected_ids:
            selected.append((app_id, raw))
            selected_ids.add(app_id)
    # Second pass: fill up to TARGET games from the rest of the file, still in that order.
    for app_id, raw in games:
        if len(selected) >= TARGET:
            break
        if app_id not in selected_ids:
            selected.append((app_id, raw))
            selected_ids.add(app_id)
    # If the needed games already passed TARGET, keep only the first TARGET.
    selected = selected[:TARGET]
    selected_ids = {app_id for app_id, _ in selected}

    # Drop a review whose game is not in the short game list. Field 1 is app_id.
    reviews = [raw for raw in reviews if next(csv.reader([raw]))[1] in selected_ids]
    # Drop a recommendation whose game is not in the short game list. Field 0 is app_id.
    recs = [raw for raw in recs if next(csv.reader([raw]))[0] in selected_ids]

    write_rows(folder, "games_clean.csv", game_header, [raw for _, raw in selected])
    write_rows(folder, "all_reviews_clean.csv", review_header, reviews)
    write_rows(folder, "recommendations_clean.csv", rec_header, recs)


# Find the folder, clean first if the cleaned files are not ready, then shorten.
# Nothing is passed in. Nothing is returned.
def main():
    folder = find_folder()
    if not folder.is_dir():
        raise SystemExit(f"Folder not found: {folder}")
    print(f"shortening CSVs in {folder}", flush=True)
    problem = cleaned_problem(folder)
    if problem:
        ask_to_clean(folder, problem)
    shorten(folder)


# Run main only when you start this file.
if __name__ == "__main__":
    main()
