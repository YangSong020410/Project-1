# USE sets NextQuest as the active schema. The tables from create-tables.sql are in that schema.
USE NextQuest;

# DELETE FROM removes rows. There is no WHERE clause, so every row in the table goes.
# Child rows go first. A parent row that a foreign key still references cannot be deleted.
DELETE FROM SteamReview;

# SteamRecommendation is also a child of Game.
DELETE FROM SteamRecommendation;

# GameGenre is a child of Game and of Genre.
DELETE FROM GameGenre;

# GameDeveloper is a child of Game and of Developer.
DELETE FROM GameDeveloper;

# Genre can be emptied now that GameGenre no longer references it.
DELETE FROM Genre;

# Developer can be emptied now that GameDeveloper no longer references it.
DELETE FROM Developer;

# Game can be emptied now that its child rows are gone.
DELETE FROM Game;

/**
Data Setup:
Python3 is required to run the scripts.
Check with: python3 --version
Install if needed with: brew install python3

Move the three CSV files into your project folder. 
Do not change the names.
Command line from your project folder:

python3 clean_csvs.py
python3 shorten_csvs.py
python3 split_games.py
python3 split_gamevideos.py
OR if using the full dataset (remember to change the cp csv filenames below):
python3 split_games.py data-clean/games_clean.csv

The files must be in the /tmp folder
its the easiest way I found to avoid server and local permission errors.
Run the following commands from your project folder to copy the files to the /tmp folder (Mac):

cp games_short_clean.csv /tmp/games_short_clean.csv
cp game_videos.csv /tmp/game_videos.csv
cp all_reviews_short_clean.csv /tmp/all_reviews_short_clean.csv
cp recommendations_short_clean.csv /tmp/recommendations_short_clean.csv
cp genres.csv /tmp/genres.csv
cp developers.csv /tmp/developers.csv
cp game_genres.csv /tmp/game_genres.csv
cp game_developers.csv /tmp/game_developers.csv
*/

# Workbench 6.3 needs the word LOCAL in front of INFILE. Workbench 8.0 and newer leaves LOCAL off.
# LOAD DATA INFILE bulk-loads the game file into Game. This is one statement through the SET clause.
# FIELDS TERMINATED BY ',' means a comma separates columns in the file.
# OPTIONALLY ENCLOSED BY '"' means a field may be wrapped in quotes, and it does not have to be.
# ESCAPED BY '' means the file does not mark a special character with a backslash.
# LINES TERMINATED BY '\n' matches a Mac line ending.
# IGNORE 1 LINES skips the header row, the first line of column names.
# A name written as @name is a session variable. It holds that field for this session so SET can use it. The value is not stored under that file name.
# A name without @ is a column of Game. The field goes straight into that column.
# SET assigns the columns that need a change before they are stored.
# LEFT is a string function. LEFT(@name, 255) keeps the first 255 characters so the name fits VARCHAR(255).
# STR_TO_DATE is a date time function. It reads @release_date and stores a DATE.
# (@windows = 'True') is TRUE when the field text is True, and FALSE otherwise. The same check sets mac and linux. Those columns are BOOLEAN.
LOAD DATA INFILE '/tmp/games_short_clean.csv'
  INTO TABLE Game
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (app_id, @name, @release_date, @estimated_owners, @peak_ccu, @required_age, price,
   @discount, @dlc_count, @about_the_game, @supported_languages, @full_audio_languages,
   @reviews, header_image, @website, @support_url, @support_email, @windows, @mac, @linux,
   metacritic_score, @metacritic_url, @user_score, positive_ratings, negative_ratings,
   @score_rank, @achievements, @recommendations, @notes, @average_playtime_forever,
   @average_playtime_two_weeks, @median_playtime_forever, @median_playtime_two_weeks,
   @developers, @publishers, @categories, @genres, @tags, @screenshots, @movies)
  SET name = LEFT(@name, 255),
      release_date = STR_TO_DATE(@release_date, '%b %e, %Y'),
      windows = (@windows = 'True'),
      mac = (@mac = 'True'),
      linux = (@linux = 'True');

# Read app_id plus the developer text and the genre text from the same file.
# DROP TABLE deletes the table definition and the data if this table is already here from an earlier run.
DROP TEMPORARY TABLE IF EXISTS GameList;

# CREATE TABLE makes GameList. TEMPORARY means MySQL drops it when this session ends.
# The table holds the two text lists so the later statements can split them into rows.
CREATE TEMPORARY TABLE GameList (
  # list_id is an INT. AUTO_INCREMENT generates a unique surrogate key, in file order.
  list_id INT AUTO_INCREMENT,
  # app_id is an INT, the same game id loaded into Game.
  app_id INT,
  # developers is a VARCHAR(600), the developer names still in one string.
  developers VARCHAR(600),
  # genres is a VARCHAR(300), the genre names still in one string.
  genres VARCHAR(300),
  # marked_developers is a VARCHAR(600). The next UPDATE writes the marked copy here.
  marked_developers VARCHAR(600),
  # marked_genres is a VARCHAR(300). The next UPDATE writes the marked copy here.
  marked_genres VARCHAR(300),
  # The primary key is list_id. It is unique and cannot be NULL.
  CONSTRAINT pk_GameList_list_id PRIMARY KEY (list_id)
);

# Bulk-load the same game file into GameList.
# developers and genres are real columns, so those two fields are stored.
# Every other field goes into a session variable and is not stored.
LOAD DATA INFILE '/tmp/games_short_clean.csv'
  INTO TABLE GameList
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (app_id, @name, @release_date, @estimated_owners, @peak_ccu, @required_age, @price,
   @discount, @dlc_count, @about_the_game, @supported_languages, @full_audio_languages,
   @reviews, @header_image, @website, @support_url, @support_email, @windows, @mac, @linux,
   @metacritic_score, @metacritic_url, @user_score, @positive_ratings, @negative_ratings,
   @score_rank, @achievements, @recommendations, @notes, @average_playtime_forever,
   @average_playtime_two_weeks, @median_playtime_forever, @median_playtime_two_weeks,
   developers, @publishers, @categories, genres, @tags, @screenshots, @movies);

# UPDATE sets two columns on every row of GameList. There is no WHERE clause, so no row is filtered out.
# REPLACE is a string function. It hides a comma that belongs inside a name, as in CAPCOM Co., Ltd., by swapping ', ' for '<,>'.
# A comma with no space after it still separates one name from the next.
UPDATE GameList
  SET marked_developers = REPLACE(developers, ', ', '<,>'),
      marked_genres = REPLACE(genres, ', ', '<,>');

# Numbers is a list of slots, 1 through 50. The longest name list in the file has 41 names, so 50 slots covers it.
DROP TEMPORARY TABLE IF EXISTS Numbers;

# n is an INT. Each row is one slot number.
CREATE TEMPORARY TABLE Numbers (
  n INT
);

# INSERT INTO adds the slot numbers 1 through 50 in one statement. Each parenthesized value is one row.
INSERT INTO Numbers(n)
  VALUES(1),(2),(3),(4),(5),(6),(7),(8),(9),(10),
  (11),(12),(13),(14),(15),(16),(17),(18),(19),(20),
  (21),(22),(23),(24),(25),(26),(27),(28),(29),(30),
  (31),(32),(33),(34),(35),(36),(37),(38),(39),(40),
  (41),(42),(43),(44),(45),(46),(47),(48),(49),(50);

# GameGenreList will hold one genre name per row, still tied to its game.
DROP TEMPORARY TABLE IF EXISTS GameGenreList;

CREATE TEMPORARY TABLE GameGenreList (
  # app_id is an INT, the game this name belongs to.
  app_id INT,
  # name is a VARCHAR(255), one genre name.
  name VARCHAR(255),
  # list_id is an INT, the GameList row this name came from.
  list_id INT,
  # n is an INT, the slot number of this name inside that list.
  n INT
);

# Insert one row per genre name on each game. INSERT INTO ... SELECT stores the result of the SELECT.
# The inner SELECT is a subquery, a nested SELECT in the FROM clause.
# INNER JOIN is an intersection. A Numbers row is kept when n is not past the last name in that game's genre list.
# CHAR_LENGTH is a string function. It counts characters. Removing the commas and subtracting leaves the comma count. Add 1 to get the number of names.
# SUBSTRING_INDEX is a string function. The inner call keeps the text through comma number n. The outer call, with -1, keeps only the last piece, which is name number n.
# REPLACE puts back a comma that belonged inside a name, the one hidden as '<,>'.
# TRIM drops spaces, then leftover commas, then spaces again.
# WHERE name <> '' is a selection. An empty name is filtered out.
# The outer SELECT projects app_id, name, list_id, and n.
INSERT INTO GameGenreList(app_id, name, list_id, n)
  SELECT app_id, name, list_id, n
  FROM (
    SELECT GameList.app_id,
           TRIM(TRIM(BOTH ',' FROM TRIM(
             REPLACE(
               SUBSTRING_INDEX(SUBSTRING_INDEX(GameList.marked_genres, ',', Numbers.n), ',', -1),
               '<,>', ', ')
           ))) AS name,
           GameList.list_id,
           Numbers.n
    FROM GameList
    INNER JOIN Numbers
      ON Numbers.n <= 1
        + CHAR_LENGTH(GameList.marked_genres)
        - CHAR_LENGTH(REPLACE(GameList.marked_genres, ',', ''))
  ) pieces
  WHERE name <> '';

# Store each genre name once, in the order it first shows up.
# GROUP BY name aggregates the rows. Each name becomes one group.
# MIN is an aggregation function. list_id * 100 + n marks the place the name was seen. MIN keeps the earliest place.
# ORDER BY sorts on that earliest place, so the insert follows first-seen order.
INSERT INTO Genre(name)
  SELECT first_names.name
  FROM (
    SELECT name, MIN(list_id * 100 + n) AS seen
    FROM GameGenreList
    GROUP BY name
  ) first_names
  ORDER BY first_names.seen;

# Match each game to genre_id and insert the pair into GameGenre.
# INNER JOIN matches GameGenreList.name to Genre.name. Those two columns are the same attribute.
# GROUP BY app_id, genre_id keeps one row when the same pair shows up more than once.
# The primary key of GameGenre is that pair, so the pair can be stored only once.
INSERT INTO GameGenre(app_id, genre_id)
  SELECT GameGenreList.app_id, Genre.genre_id
  FROM GameGenreList
  INNER JOIN Genre ON Genre.name = GameGenreList.name
  GROUP BY GameGenreList.app_id, Genre.genre_id;

# The genre names are now in Genre and GameGenre. Drop the working table.
DROP TEMPORARY TABLE GameGenreList;

# Do the same split for developer names.
DROP TEMPORARY TABLE IF EXISTS GameDeveloperList;

CREATE TEMPORARY TABLE GameDeveloperList (
  # app_id is an INT, the game this developer name belongs to.
  app_id INT,
  # name is a VARCHAR(255), one developer name.
  name VARCHAR(255),
  # list_id is an INT, the GameList row this name came from.
  list_id INT,
  # n is an INT, the slot of this name in that game's developer list.
  n INT
);

# Same split as the genre insert. The string functions read marked_developers instead of marked_genres.
# INNER JOIN stops at the last developer name. WHERE drops an empty name.
INSERT INTO GameDeveloperList(app_id, name, list_id, n)
  SELECT app_id, name, list_id, n
  FROM (
    SELECT GameList.app_id,
           TRIM(TRIM(BOTH ',' FROM TRIM(
             REPLACE(
               SUBSTRING_INDEX(SUBSTRING_INDEX(GameList.marked_developers, ',', Numbers.n), ',', -1),
               '<,>', ', ')
           ))) AS name,
           GameList.list_id,
           Numbers.n
    FROM GameList
    INNER JOIN Numbers
      ON Numbers.n <= 1
        + CHAR_LENGTH(GameList.marked_developers)
        - CHAR_LENGTH(REPLACE(GameList.marked_developers, ',', ''))
  ) pieces
  WHERE name <> '';

# Store each developer name once. GROUP BY name makes one group per name.
# MIN keeps the earliest place that name showed up. ORDER BY inserts in that order.
INSERT INTO Developer(name)
  SELECT first_names.name
  FROM (
    SELECT name, MIN(list_id * 100 + n) AS seen
    FROM GameDeveloperList
    GROUP BY name
  ) first_names
  ORDER BY first_names.seen;

# Match each game to developer_id. GROUP BY the pair so a repeated name on one game is inserted once.
INSERT INTO GameDeveloper(app_id, developer_id)
  SELECT GameDeveloperList.app_id, Developer.developer_id
  FROM GameDeveloperList
  INNER JOIN Developer ON Developer.name = GameDeveloperList.name
  GROUP BY GameDeveloperList.app_id, Developer.developer_id;

# The working tables are no longer needed. DROP TABLE deletes the definition and the data.
DROP TEMPORARY TABLE GameDeveloperList;
DROP TEMPORARY TABLE Numbers;
DROP TEMPORARY TABLE GameList;

# Bulk-load the review file into SteamReview.
# Lines in this file end with '\r\n'.
# Columns without @ are stored as they appear. Columns with @ are session variables for the SET clause.
# SET divides @author_playtime_at_review by 60 and stores hours in hours_played. The file value is minutes.
# FROM_UNIXTIME is a date time function. @timestamp_created is seconds since the unix epoch. The function stores that as review_date.
LOAD DATA INFILE '/tmp/all_reviews_short_clean.csv'
  INTO TABLE SteamReview
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
  LINES TERMINATED BY '\r\n'
  IGNORE 1 LINES
  (steam_review_id, app_id, @game, author_steamid, @author_num_games_owned,
   @author_num_reviews, @author_playtime_forever, @author_playtime_last_two_weeks,
   @author_playtime_at_review, @author_last_played, language, @review,
   @timestamp_created, @timestamp_updated, is_recommended, @votes_up, @votes_funny,
   @weighted_vote_score, @comment_count, @steam_purchase, @received_for_free,
   @written_during_early_access, @hidden_in_steam_china, @steam_china_location)
  SET hours_played = @author_playtime_at_review / 60,
      review_date = FROM_UNIXTIME(@timestamp_created);

# The first recommendation id in the file is 0.
# AUTO_INCREMENT would turn that 0 into 1. The next row would then use the same primary key value.
# SET assigns sql_mode for this session. @@sql_mode holds the current mode.
# CONCAT is a string function. It adds NO_AUTO_VALUE_ON_ZERO to that mode so the loaded 0 stays 0.
SET SESSION sql_mode = CONCAT(@@sql_mode, ',NO_AUTO_VALUE_ON_ZERO');

# Bulk-load the recommendation file into SteamRecommendation.
# steam_recommendation_id is loaded from the file, including the 0 from the line above.
# SET stores TRUE in is_recommended when the field text is true, and FALSE otherwise.
LOAD DATA INFILE '/tmp/recommendations_short_clean.csv'
  INTO TABLE SteamRecommendation
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (app_id, @helpful, @funny, recommendation_date, @is_recommended, hours_played,
   author_id, steam_recommendation_id)
  SET is_recommended = (@is_recommended = 'true');

# GameVideo: screenshot rows generated by split_gamevideos.py from the
# Screenshots column (the Movies column is empty in this dataset).
LOAD DATA INFILE '/tmp/game_videos.csv'
  INTO TABLE GameVideo
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (app_id, name, url, video_type);

# One result set, one row per table.
# COUNT(*) is an aggregation function. It counts the rows in that table.
# AS renames the constant to table_name and renames the count to row_count.
# UNION ALL stacks the SELECT results and keeps every row. UNION DISTINCT would remove duplicate rows. These counts should all stay.
SELECT 'User' AS table_name, COUNT(*) AS row_count FROM User
UNION ALL SELECT 'Genre', COUNT(*) FROM Genre
UNION ALL SELECT 'Developer', COUNT(*) FROM Developer
UNION ALL SELECT 'Game', COUNT(*) FROM Game
UNION ALL SELECT 'GameVideo', COUNT(*) FROM GameVideo
UNION ALL SELECT 'SavedGame', COUNT(*) FROM SavedGame
UNION ALL SELECT 'Review', COUNT(*) FROM Review
UNION ALL SELECT 'RecommendationSurvey', COUNT(*) FROM RecommendationSurvey
UNION ALL SELECT 'GameGenre', COUNT(*) FROM GameGenre
UNION ALL SELECT 'GameDeveloper', COUNT(*) FROM GameDeveloper
UNION ALL SELECT 'SteamRecommendation', COUNT(*) FROM SteamRecommendation
UNION ALL SELECT 'SteamReview', COUNT(*) FROM SteamReview;
