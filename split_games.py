#!/usr/bin/env python3
"""Split the Developers and Genres columns of a cleaned games CSV.

Run after shorten_csvs.py, from the project folder:

    python3 split_games.py
    python3 split_games.py games_clean.csv

With no argument it reads games_short_clean.csv. Pass the name of a games
CSV to split a different one, such as the full cleaned file. The four
output files are written next to the input:

- genres.csv           name
- developers.csv       name
- game_genres.csv      app_id, name
- game_developers.csv  app_id, name

The SQL file assigns genre_id and developer_id. Running this again
overwrites the four files.

Every field is quoted, so LOAD DATA uses ENCLOSED BY '"'.
"""

import csv
import sys
import re
from pathlib import Path

csv.field_size_limit(100_000_000)

DEVELOPERS = 33
GENRES = 36
DEFAULT_NAME = "games_short_clean.csv"


def find_source():
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).expanduser().resolve()
    for folder in (Path.cwd(), Path(__file__).resolve().parent):
        candidate = folder / DEFAULT_NAME
        if candidate.is_file():
            return candidate
    return Path.cwd() / DEFAULT_NAME


def split_names(field):
    names = []
    for name in re.split(r",(?=\S)", field):
        name = name.strip().strip(",").strip()
        if name and name not in names:
            names.append(name)
    return names


def write(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    print(f"wrote {path.name}")


def main():
    source = find_source()
    if not source.is_file():
        raise SystemExit(
            f"{source} not found.\n"
            "Run clean_csvs.py and shorten_csvs.py first, or pass the name of a games CSV:\n"
            "    python3 split_games.py games_clean.csv"
        )
    folder = source.parent

    genre_names = []
    seen_genres = set()
    developer_names = []
    seen_developers = set()
    game_genres = []
    game_developers = []

    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            app_id = row[0]
            for name in split_names(row[GENRES]):
                if name not in seen_genres:
                    seen_genres.add(name)
                    genre_names.append((name,))
                game_genres.append((app_id, name))
            for name in split_names(row[DEVELOPERS]):
                if name not in seen_developers:
                    seen_developers.add(name)
                    developer_names.append((name,))
                game_developers.append((app_id, name))

    print(f"read {source.name}: {len(genre_names)} genres, {len(developer_names)} developers")
    write(folder / "genres.csv", ("name",), genre_names)
    write(folder / "developers.csv", ("name",), developer_names)
    write(folder / "game_genres.csv", ("app_id", "name"), game_genres)
    write(folder / "game_developers.csv", ("app_id", "name"), game_developers)


if __name__ == "__main__":
    main()