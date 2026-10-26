USE NextQuest;
DELETE FROM SteamReview;
DELETE FROM SteamRecommendation;
DELETE FROM GameGenre;
DELETE FROM GameDeveloper;
DELETE FROM Genre;
DELETE FROM Developer;
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

# Workbench 6.3 needs LOCAL. Workbench 8.0+ leaves it off.
# Load each game. SET shortens the name, reads the date, and stores the flags.
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

# Read app_id plus the developer and genre text from the same file.
DROP TEMPORARY TABLE IF EXISTS GameList;
CREATE TEMPORARY TABLE GameList (
  list_id INT AUTO_INCREMENT,
  app_id INT,
  developers VARCHAR(600),
  genres VARCHAR(300),
  marked_developers VARCHAR(600),
  marked_genres VARCHAR(300),
  CONSTRAINT pk_GameList_list_id PRIMARY KEY (list_id)
);
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

# Hide a comma that belongs to the name, as in CAPCOM Co., Ltd.
UPDATE GameList
  SET marked_developers = REPLACE(developers, ', ', '<,>'),
      marked_genres = REPLACE(genres, ', ', '<,>');

# Count off name slots. The longest list in the file has 41 names.
DROP TEMPORARY TABLE IF EXISTS Numbers;
CREATE TEMPORARY TABLE Numbers (
  n INT
);
INSERT INTO Numbers(n)
  VALUES(1),(2),(3),(4),(5),(6),(7),(8),(9),(10),
  (11),(12),(13),(14),(15),(16),(17),(18),(19),(20),
  (21),(22),(23),(24),(25),(26),(27),(28),(29),(30),
  (31),(32),(33),(34),(35),(36),(37),(38),(39),(40),
  (41),(42),(43),(44),(45),(46),(47),(48),(49),(50);

# Pull each genre name out of the list.
DROP TEMPORARY TABLE IF EXISTS GameGenreList;
CREATE TEMPORARY TABLE GameGenreList (
  app_id INT,
  name VARCHAR(255),
  list_id INT,
  n INT
);
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
INSERT INTO Genre(name)
  SELECT first_names.name
  FROM (
    SELECT name, MIN(list_id * 100 + n) AS seen
    FROM GameGenreList
    GROUP BY name
  ) first_names
  ORDER BY first_names.seen;

# Match each game to genre_id.
INSERT INTO GameGenre(app_id, genre_id)
  SELECT GameGenreList.app_id, Genre.genre_id
  FROM GameGenreList
  INNER JOIN Genre ON Genre.name = GameGenreList.name
  GROUP BY GameGenreList.app_id, Genre.genre_id;
DROP TEMPORARY TABLE GameGenreList;

# Pull each developer name out of the list.
DROP TEMPORARY TABLE IF EXISTS GameDeveloperList;
CREATE TEMPORARY TABLE GameDeveloperList (
  app_id INT,
  name VARCHAR(255),
  list_id INT,
  n INT
);
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

# Store each developer name once, in the order it first shows up.
INSERT INTO Developer(name)
  SELECT first_names.name
  FROM (
    SELECT name, MIN(list_id * 100 + n) AS seen
    FROM GameDeveloperList
    GROUP BY name
  ) first_names
  ORDER BY first_names.seen;

# Match each game to developer_id. One pair when a name repeats.
INSERT INTO GameDeveloper(app_id, developer_id)
  SELECT GameDeveloperList.app_id, Developer.developer_id
  FROM GameDeveloperList
  INNER JOIN Developer ON Developer.name = GameDeveloperList.name
  GROUP BY GameDeveloperList.app_id, Developer.developer_id;

DROP TEMPORARY TABLE GameDeveloperList;
DROP TEMPORARY TABLE Numbers;
DROP TEMPORARY TABLE GameList;

# Load the reviews. SET turns minutes into hours and Unix time into a date.
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

# The first recommendation id is 0. Without this, AUTO_INCREMENT stores that 0 as 1,
# colliding with the next rows primary key. This keeps the value at 0.
SET SESSION sql_mode = CONCAT(@@sql_mode, ',NO_AUTO_VALUE_ON_ZERO');
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

# Display the row counts for each table.
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
