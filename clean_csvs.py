#!/usr/bin/env python3
"""Clean freshly downloaded NextQuest Steam CSVs.

Put these three files in the same folder as this script (or pass that folder
as an argument) and run:

    python3 clean_csvs.py

The script writes games_clean.csv, recommendations_clean.csv, and
all_reviews_clean.csv next to the originals. It keeps each source file.

A row is dropped when LOAD DATA would reject it:

- games.csv: not 40 fields, a bad app id, a repeated app id, or a price,
  Metacritic score, or rating count that is not a number.
- all_reviews.csv: not 24 fields, a bad review id, an app id that is not
  in the kept games, a bad Steam id, a non-numeric voted_up value, or a
  language longer than 255 characters. A repeated review id is dropped
  only after one row for that id has been kept, so a copy whose game is
  missing does not block a later copy whose game is in the file.
- recommendations.csv: not 8 fields, an app id that is not in the kept games,
  a bad date or hours value, a bad user id, a bad recommendation id, or a
  repeated recommendation id.

Reviews stay on Windows line endings. Games and recommendations stay on
Unix line endings. Quoted fields that contain line breaks are kept whole.
"""

import csv
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

csv.field_size_limit(100_000_000)

INT_MIN = -2147483648
INT_MAX = 2147483647
BI_MIN = -9223372036854775808
BI_MAX = 9223372036854775807
MAX_RECORD = 32 * 1024 * 1024

SOURCES = ("games.csv", "recommendations.csv", "all_reviews.csv")


class ProgressBar:
    """Byte progress on stderr. A tty redraws one line; a log gets a line every 2%."""

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


def clean_name(filename):
    path = Path(filename)
    return f"{path.stem}_clean{path.suffix}"


def find_folder():
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).expanduser().resolve()
    needed = SOURCES
    cwd = Path.cwd()
    if all((cwd / name).is_file() for name in needed):
        return cwd
    here = Path(__file__).resolve().parent
    if all((here / name).is_file() for name in needed):
        return here
    return cwd


def is_int(value, lo, hi):
    if not value or re.fullmatch(r"[+-]?\d+", value) is None:
        return False
    number = int(value)
    return lo <= number <= hi


def is_decimal(value):
    return bool(value) and re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", value) is not None


def is_date(value):
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or "") is None:
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


class IdSet:
    """Seen-set for ids in 0..2147483647. One bit per id, about 256 MiB."""

    def __init__(self):
        self.bits = bytearray(1 << 28)

    def add_if_new(self, number):
        if number < 0 or number > INT_MAX:
            return False
        index = number >> 3
        mask = 1 << (number & 7)
        if self.bits[index] & mask:
            return False
        self.bits[index] |= mask
        return True


def read_record(handle):
    parts = []
    quotes = 0
    size = 0
    oversized = False
    while True:
        line = handle.readline()
        if not line:
            return None, oversized
        parts.append(line)
        quotes += line.count('"')
        size += len(line)
        if quotes % 2 == 0:
            return "".join(parts), oversized
        if size > MAX_RECORD:
            oversized = True
            while quotes % 2 != 0:
                line = handle.readline()
                if not line:
                    return None, True
                quotes += line.count('"')
            return None, True


def game_row_bad(row, seen):
    if len(row) != 40:
        return "fields"
    if not is_int(row[0], 0, INT_MAX):
        return "app_id"
    app_id = int(row[0])
    if app_id in seen:
        return "duplicate_app_id"
    if not is_decimal(row[6]):
        return "price"
    if not is_int(row[20], INT_MIN, INT_MAX):
        return "metacritic_score"
    if not is_int(row[23], INT_MIN, INT_MAX):
        return "positive_ratings"
    if not is_int(row[24], INT_MIN, INT_MAX):
        return "negative_ratings"
    seen.add(app_id)
    return None


def review_row_bad(row, games, seen_ids):
    if len(row) != 24:
        return "fields"
    if not is_int(row[0], 0, INT_MAX):
        return "steam_review_id"
    if not is_int(row[1], 0, INT_MAX) or int(row[1]) not in games:
        return "app_id"
    if not is_int(row[3], BI_MIN, BI_MAX):
        return "author_steamid"
    if not is_int(row[14], INT_MIN, INT_MAX):
        return "is_recommended"
    if len(row[10]) > 255:
        return "language"
    # A copy whose game is missing must not block the same review id
    # on a later row whose game is in the file.
    if not seen_ids.add_if_new(int(row[0])):
        return "duplicate_steam_review_id"
    return None


def recommendation_row_bad(row, games, seen_ids):
    if len(row) != 8:
        return "fields"
    if not is_int(row[0], 0, INT_MAX) or int(row[0]) not in games:
        return "app_id"
    if not is_date(row[3]):
        return "recommendation_date"
    if not is_decimal(row[5]):
        return "hours_played"
    if not is_int(row[6], INT_MIN, INT_MAX):
        return "author_id"
    if not is_int(row[7], 0, INT_MAX):
        return "steam_recommendation_id"
    if not seen_ids.add_if_new(int(row[7])):
        return "duplicate_steam_recommendation_id"
    return None


def clean_file(folder, name, keep_row):
    source = folder / name
    dest = folder / clean_name(name)
    temp = dest.with_suffix(dest.suffix + ".cleaning")
    kept = 0
    dropped = 0
    reasons = Counter()
    seen_records = 0
    bar = ProgressBar(name, source.stat().st_size)
    print(f"start {name}", flush=True)
    with source.open("r", encoding="utf-8", errors="replace", newline="") as src, temp.open(
        "w", encoding="utf-8", newline="", buffering=8 * 1024 * 1024
    ) as out:
        header, oversized = read_record(src)
        if header is None or oversized:
            temp.unlink(missing_ok=True)
            bar.close()
            raise SystemExit(f"{name} has no usable header")
        out.write(header)
        while True:
            raw, oversized = read_record(src)
            if raw is None and not oversized:
                break
            seen_records += 1
            if oversized or raw is None:
                dropped += 1
                reasons["oversize"] += 1
            else:
                reason = keep_row(next(csv.reader([raw])))
                if reason is None:
                    out.write(raw)
                    kept += 1
                else:
                    dropped += 1
                    reasons[reason] += 1
            if seen_records % 5000 == 0:
                bar.update(byte_pos(src), f"kept {kept:,}  dropped {dropped:,}")
        bar.update(source.stat().st_size, f"kept {kept:,}  dropped {dropped:,}")
    bar.close()
    temp.replace(dest)
    print(f"done {dest.name} kept {kept} dropped {dropped} reasons {dict(reasons)}", flush=True)
    return kept, dropped


def main():
    folder = find_folder()
    missing = [name for name in SOURCES if not (folder / name).is_file()]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(
            f"Put {joined} in {folder} and run this script again.\n"
            "It writes games_clean.csv, recommendations_clean.csv, and all_reviews_clean.csv."
        )

    print(f"cleaning CSVs in {folder}", flush=True)
    games = set()

    def check_game(row):
        return game_row_bad(row, games)

    clean_file(folder, "games.csv", check_game)
    print(f"games kept {len(games)}", flush=True)

    review_ids = IdSet()

    def check_review(row):
        return review_row_bad(row, games, review_ids)

    clean_file(folder, "all_reviews.csv", check_review)
    del review_ids

    recommendation_ids = IdSet()

    def check_recommendation(row):
        return recommendation_row_bad(row, games, recommendation_ids)

    clean_file(folder, "recommendations.csv", check_recommendation)


if __name__ == "__main__":
    main()
