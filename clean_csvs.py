#!/usr/bin/env python3
# Run this file with python3. It cleans the three Steam files so LOAD DATA INFILE can load them.

"""Clean the three Steam files before they are loaded.

Put games.csv, recommendations.csv, and all_reviews.csv in this folder and run:

    python3 clean_csvs.py

This writes games_clean.csv, recommendations_clean.csv, and all_reviews_clean.csv
beside the originals. The original files stay.

A row is dropped when it would break a column in create-tables.sql.

games.csv must have 40 fields. app_id must be an INT from 0 to 2147483647, once.
price must be a fixed-point number. The Metacritic score and both rating counts
must be INT values.

all_reviews.csv must have 24 fields. The review id and app_id must be INT values.
app_id must be a game that was kept. The Steam id must fit in a BIGINT.
The recommended flag must be an INT. language must fit in VARCHAR(255), 255 characters.
A repeated review id is dropped only after one good row for that id is kept.
A copy whose game is missing does not block a later copy whose game was kept.

recommendations.csv must have 8 fields. app_id must be a kept game.
The date must be a DATE, YYYY-MM-DD. Hours must be a fixed-point number.
The author id must be an INT. The recommendation id must be an INT from 0 to
2147483647, and that id can occur only once.

Review rows keep Windows line endings. Game rows and recommendation rows keep
Mac line endings. A quoted field that contains a line break stays one row.
"""

# csv reads a comma-separated row and splits it into fields.
import csv
# re checks whether a whole field matches a simple text pattern.
import re
# sys holds the words typed after python3, and the place error messages are printed.
import sys
# time supplies a clock, used to avoid redrawing the progress line too often.
import time
# Counter counts how many rows were dropped for each reason.
from collections import Counter
# datetime checks that a YYYY-MM-DD text is a real date.
from datetime import datetime
# Path is a file location. It can test whether a file is there and open it.
from pathlib import Path

# A single field may be very long. Raise the limit so a long description is not rejected.
csv.field_size_limit(100_000_000)

# Smallest and largest INT, the 32-bit number from the data-type notes.
INT_MIN = -2147483648
INT_MAX = 2147483647
# Smallest and largest BIGINT, the 64-bit number. A Steam id needs this wider range.
BI_MIN = -9223372036854775808
BI_MAX = 9223372036854775807
# A row longer than this many characters is dropped. 32 * 1024 * 1024 is 32 million characters.
MAX_RECORD = 32 * 1024 * 1024

# The three source file names. They must sit in the folder this script searches.
SOURCES = ("games.csv", "recommendations.csv", "all_reviews.csv")


# Draw a progress line while a file is read.
# label is text, the name printed on the line.
# total is an int, how much work the line represents.
# Nothing is returned.
class ProgressBar:
    # Save the name and the total on this bar.
    # label is text. total is an int. Nothing is returned.
    def __init__(self, label, total):
        # Keep the name that will be printed.
        self.label = label
        # Keep the total. Use at least 1 so a later division never divides by zero.
        self.total = max(int(total), 1)
        # True when messages go to a screen you are watching. False when they go to a saved log.
        self.tty = sys.stderr.isatty()
        # last_draw is the clock time of the previous redraw. 0.0 means none yet.
        self.last_draw = 0.0
        # last_bucket is the last progress step that was printed. -1 means none yet.
        self.last_bucket = -1

    # Reprint the line when enough time, or enough progress, has passed.
    # current is an int, how far the work has gotten. detail is extra text for the end of the line.
    # Nothing is returned.
    def update(self, current, detail=""):
        # frac is the share finished, held between 0 and 1.
        frac = min(1.0, current / self.total)
        # now is the current clock time.
        now = time.monotonic()
        # bucket cuts that share into 50 steps.
        bucket = int(frac * 50)
        # On a live screen, skip the redraw if the last one was under a tenth of a second ago.
        if self.tty:
            if now - self.last_draw < 0.1 and frac < 1:
                return
        # In a log, print again only when the step number changes.
        elif bucket == self.last_bucket and frac < 1:
            return
        # Remember this redraw.
        self.last_draw = now
        self.last_bucket = bucket
        # A live screen rewrites the same line. A log starts a new line.
        self._draw(frac, detail, end="\r" if self.tty else "\n")

    # Wipe the progress line off a live screen. Nothing is returned.
    def close(self):
        if self.tty:
            # Print spaces over the old line, then return to the start of it.
            print("\r" + " " * 110 + "\r", end="", file=sys.stderr, flush=True)

    # Print one progress line.
    # frac is the share finished, from 0 to 1. detail is extra text. end is how the line closes.
    # Nothing is returned.
    def _draw(self, frac, detail, end):
        # The bar is 30 marks wide.
        width = 30
        # filled is how many of those marks are done.
        filled = int(width * frac)
        # # is finished work. - is work still left.
        bar = "#" * filled + "-" * (width - filled)
        # Build the visible text: name, bar, percent, and the extra detail.
        text = f"{self.label} [{bar}] {frac * 100:5.1f}% {detail}"
        # A live screen starts by jumping back to column 1. A log does not.
        prefix = "\r" if self.tty else ""
        # Print at most 108 characters, to the error stream, and push it out immediately.
        print(f"{prefix}{text[:108]}", end=end, file=sys.stderr, flush=True)


# Return how many bytes have been read, as an int.
# handle is the open file.
def byte_pos(handle):
    # The byte count lives on the underlying file, when this text file has one.
    buffer = getattr(handle, "buffer", None)
    if buffer is not None:
        return buffer.tell()
    # If there is no underlying file, report 0.
    return 0


# Return the cleaned file name, as text.
# filename is text, such as games.csv. games.csv becomes games_clean.csv.
def clean_name(filename):
    path = Path(filename)
    return f"{path.stem}_clean{path.suffix}"


# Return the folder that holds the three source files, as a Path.
# If you typed a folder after the script name, that folder is used.
def find_folder():
    # sys.argv is the list of words typed. Word 0 is the script. Word 1, if present, is a folder.
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).expanduser().resolve()
    needed = SOURCES
    # Start with the folder you ran the command from.
    cwd = Path.cwd()
    if all((cwd / name).is_file() for name in needed):
        return cwd
    # Otherwise use the folder this script itself is in.
    here = Path(__file__).resolve().parent
    if all((here / name).is_file() for name in needed):
        return here
    # If neither folder has the files, still return the folder you ran from. main will report the miss.
    return cwd


# Return True when value is a whole number between lo and hi. Otherwise return False.
# value is text from one field. lo and hi are ints, the smallest and largest allowed.
def is_int(value, lo, hi):
    # An empty field is not an INT. The pattern asks for an optional + or -, then digits, and nothing else.
    if not value or re.fullmatch(r"[+-]?\d+", value) is None:
        return False
    number = int(value)
    return lo <= number <= hi


# Return True when value is a fixed-point number. Otherwise return False.
# value is text. A leading sign is allowed. Digits may sit on either side of the decimal point.
def is_decimal(value):
    return bool(value) and re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", value) is not None


# Return True when value is a real DATE in YYYY-MM-DD form. Otherwise return False.
# value is text.
def is_date(value):
    # Four digits, a dash, two digits, a dash, two digits. Anything else is not this DATE form.
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or "") is None:
        return False
    # Reject a pattern that is not a real calendar day, such as month 13.
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


# Remember which INT ids have already been kept.
# One yes/no mark per id from 0 through 2147483647.
class IdSet:
    # Build the marks. Nothing is passed in. Nothing is returned.
    def __init__(self):
        # 1 << 28 slots. Eight ids share each slot, which covers every INT from 0 up.
        self.bits = bytearray(1 << 28)

    # Return True if this id is new and is now marked. Return False if it was already marked, or it is out of range.
    # number is an int, the id.
    def add_if_new(self, number):
        # Ids outside the INT range are not stored.
        if number < 0 or number > INT_MAX:
            return False
        # Pick the slot. Eight ids share one slot.
        index = number >> 3
        # Pick this id's yes/no mark inside that slot.
        mask = 1 << (number & 7)
        # The mark is already on, so this id was seen before.
        if self.bits[index] & mask:
            return False
        # Turn the mark on. The caller keeps this row.
        self.bits[index] |= mask
        return True


# Read one csv record, including a quoted field that spans several physical lines.
# handle is the open file.
# Return the record text, or None at the end of the file. Also return True when the record was too long.
def read_record(handle):
    # parts collects the physical lines that belong to this one record.
    parts = []
    # quotes counts quote characters. An even count means the record is closed.
    quotes = 0
    # size is how many characters this record has so far.
    size = 0
    oversized = False
    while True:
        # Read the next physical line. An empty result means the file ended.
        line = handle.readline()
        if not line:
            return None, oversized
        parts.append(line)
        quotes += line.count('"')
        size += len(line)
        # An even number of quotes means every quoted field is closed. This record is complete.
        if quotes % 2 == 0:
            return "".join(parts), oversized
        # Past the size cap, skip the rest of this record and tell the caller to drop it.
        if size > MAX_RECORD:
            oversized = True
            while quotes % 2 != 0:
                line = handle.readline()
                if not line:
                    return None, True
                quotes += line.count('"')
            return None, True


# Return None when this games.csv row can be kept. Otherwise return a short text reason to drop it.
# row is a list of text fields. seen is a set of app_id values already kept.
def game_row_bad(row, seen):
    # Game rows have 40 fields. A different count cannot line up with the LOAD DATA column list.
    if len(row) != 40:
        return "fields"
    # app_id must be an INT from 0 through 2147483647. That matches the Game.app_id column.
    if not is_int(row[0], 0, INT_MAX):
        return "app_id"
    app_id = int(row[0])
    # The same app_id cannot be loaded twice. Game.app_id is the primary key.
    if app_id in seen:
        return "duplicate_app_id"
    # price must be a fixed-point number, for the DECIMAL column.
    if not is_decimal(row[6]):
        return "price"
    # metacritic_score must fit in an INT.
    if not is_int(row[20], INT_MIN, INT_MAX):
        return "metacritic_score"
    # positive_ratings must fit in an INT.
    if not is_int(row[23], INT_MIN, INT_MAX):
        return "positive_ratings"
    # negative_ratings must fit in an INT.
    if not is_int(row[24], INT_MIN, INT_MAX):
        return "negative_ratings"
    # The row passed. Remember its app_id so a later copy is dropped.
    seen.add(app_id)
    return None


# Return None when this review row can be kept. Otherwise return a short text reason.
# row is a list of text fields. games is the set of kept app ids.
# seen_ids is an IdSet of review ids already kept.
def review_row_bad(row, games, seen_ids):
    # Review rows have 24 fields.
    if len(row) != 24:
        return "fields"
    # steam_review_id must be an INT from 0 through 2147483647.
    if not is_int(row[0], 0, INT_MAX):
        return "steam_review_id"
    # app_id must be an INT, and that game must be one games.csv kept.
    if not is_int(row[1], 0, INT_MAX) or int(row[1]) not in games:
        return "app_id"
    # author_steamid must fit in a BIGINT.
    if not is_int(row[3], BI_MIN, BI_MAX):
        return "author_steamid"
    # The recommended flag is stored as an INT in this file.
    if not is_int(row[14], INT_MIN, INT_MAX):
        return "is_recommended"
    # language is a VARCHAR(255). Longer text would not fit.
    if len(row[10]) > 255:
        return "language"
    # Mark the review id only after the checks above pass.
    # A copy whose game is missing returns before this line, so it does not block a later copy of the same id.
    if not seen_ids.add_if_new(int(row[0])):
        return "duplicate_steam_review_id"
    return None


# Return None when this recommendation row can be kept. Otherwise return a short text reason.
# row is a list of text fields. games is the set of kept app ids.
# seen_ids is an IdSet of recommendation ids already kept.
def recommendation_row_bad(row, games, seen_ids):
    # Recommendation rows have 8 fields.
    if len(row) != 8:
        return "fields"
    # app_id must be an INT and a game that was kept.
    if not is_int(row[0], 0, INT_MAX) or int(row[0]) not in games:
        return "app_id"
    # recommendation_date must be a DATE, YYYY-MM-DD.
    if not is_date(row[3]):
        return "recommendation_date"
    # hours_played must be a fixed-point number, for the DECIMAL column.
    if not is_decimal(row[5]):
        return "hours_played"
    # author_id must fit in an INT.
    if not is_int(row[6], INT_MIN, INT_MAX):
        return "author_id"
    # steam_recommendation_id must be an INT from 0 through 2147483647.
    if not is_int(row[7], 0, INT_MAX):
        return "steam_recommendation_id"
    # A repeated recommendation id is dropped. The first one was already marked.
    if not seen_ids.add_if_new(int(row[7])):
        return "duplicate_steam_recommendation_id"
    return None


# Read one source file, drop bad rows, and write the cleaned file.
# folder is a Path. name is text, the source file name.
# keep_row is a function. It takes the field list and returns None to keep the row, or text to drop it.
# Return two ints: how many rows were kept, and how many were dropped.
def clean_file(folder, name, keep_row):
    source = folder / name
    dest = folder / clean_name(name)
    # Write to a side file first. The real cleaned name is used only after the read finishes.
    temp = dest.with_suffix(dest.suffix + ".cleaning")
    kept = 0
    dropped = 0
    # reasons counts drops by the short text from keep_row.
    reasons = Counter()
    seen_records = 0
    # The bar's total is the file size in bytes.
    bar = ProgressBar(name, source.stat().st_size)
    print(f"start {name}", flush=True)
    # Open the source for reading and the side file for writing.
    # errors="replace" swaps a bad character for a stand-in instead of stopping.
    # newline="" leaves line endings unchanged, so Windows and Mac endings stay as they were.
    with source.open("r", encoding="utf-8", errors="replace", newline="") as src, temp.open(
        "w", encoding="utf-8", newline="", buffering=8 * 1024 * 1024
    ) as out:
        # The first record is the header, the column names. It is copied, not checked as data.
        header, oversized = read_record(src)
        if header is None or oversized:
            # Remove the side file and stop. There is nothing useful to load.
            temp.unlink(missing_ok=True)
            bar.close()
            raise SystemExit(f"{name} has no usable header")
        out.write(header)
        while True:
            # Read the next data record.
            raw, oversized = read_record(src)
            # None with oversized False means the file ended.
            if raw is None and not oversized:
                break
            seen_records += 1
            # A record past the size cap is counted and skipped.
            if oversized or raw is None:
                dropped += 1
                reasons["oversize"] += 1
            else:
                # Split this one record into fields, then ask keep_row whether to drop it.
                reason = keep_row(next(csv.reader([raw])))
                if reason is None:
                    # Keep the original text, including its line ending.
                    out.write(raw)
                    kept += 1
                else:
                    dropped += 1
                    reasons[reason] += 1
            # Refresh the progress line every 5,000 records.
            if seen_records % 5000 == 0:
                bar.update(byte_pos(src), f"kept {kept:,}  dropped {dropped:,}")
        # Draw the finished line at 100 percent.
        bar.update(source.stat().st_size, f"kept {kept:,}  dropped {dropped:,}")
    bar.close()
    # Swap the finished side file into the cleaned name.
    temp.replace(dest)
    print(f"done {dest.name} kept {kept} dropped {dropped} reasons {dict(reasons)}", flush=True)
    return kept, dropped


# Clean the three files in order. Games go first, because reviews and recommendations must name a kept game.
# Nothing is passed in. Nothing is returned.
def main():
    folder = find_folder()
    # missing is the list of source names that are not in that folder.
    missing = [name for name in SOURCES if not (folder / name).is_file()]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(
            f"Put {joined} in {folder} and run this script again.\n"
            "It writes games_clean.csv, recommendations_clean.csv, and all_reviews_clean.csv."
        )

    print(f"cleaning CSVs in {folder}", flush=True)
    # games will hold each kept app_id. Later files use this set.
    games = set()

    # row is a list of text fields. Return None to keep it, or a short reason to drop it.
    def check_game(row):
        return game_row_bad(row, games)

    clean_file(folder, "games.csv", check_game)
    print(f"games kept {len(games)}", flush=True)

    # review_ids remembers review ids already kept.
    review_ids = IdSet()

    # row is a list of text fields. Return None to keep it, or a short reason to drop it.
    def check_review(row):
        return review_row_bad(row, games, review_ids)

    clean_file(folder, "all_reviews.csv", check_review)
    # The review id marks are no longer needed. Drop them before the recommendation pass.
    del review_ids

    recommendation_ids = IdSet()

    # row is a list of text fields. Return None to keep it, or a short reason to drop it.
    def check_recommendation(row):
        return recommendation_row_bad(row, games, recommendation_ids)

    clean_file(folder, "recommendations.csv", check_recommendation)


# Run main only when you start this file. Another file can import the checks above without cleaning.
if __name__ == "__main__":
    main()
