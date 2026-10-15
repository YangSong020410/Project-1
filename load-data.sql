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
OR if using the full dataset (remember to change the cp names below):
python3 split_games.py data-clean/games_clean.csv

The files must be in the /tmp folder
its the easiest way I found to avoid server and local permission errors.
Run the following commands from your project folder to copy the files to the /tmp folder (Mac):

cp games_short_clean.csv /tmp/games_short_clean.csv
cp all_reviews_short_clean.csv /tmp/all_reviews_short_clean.csv
cp recommendations_short_clean.csv /tmp/recommendations_short_clean.csv
cp genres.csv /tmp/genres.csv
cp developers.csv /tmp/developers.csv
cp game_genres.csv /tmp/game_genres.csv
cp game_developers.csv /tmp/game_developers.csv
*/

DROP TEMPORARY TABLE IF EXISTS GameList;
CREATE TEMPORARY TABLE GameList (
  app_id INT,
  developers VARCHAR(600),
  genres VARCHAR(255)
);

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

# Load the names first. AUTO_INCREMENT assigns genre_id and developer_id.
LOAD DATA INFILE '/tmp/genres.csv' INTO TABLE Genre
  FIELDS TERMINATED BY ',' ENCLOSED BY '"'
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (name);

LOAD DATA INFILE '/tmp/developers.csv' INTO TABLE Developer
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' ESCAPED BY ''
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (name);

# Hold app_id and the genre name until the join finds genre_id.
DROP TEMPORARY TABLE IF EXISTS GameGenreList;
CREATE TEMPORARY TABLE GameGenreList (
  app_id INT,
  name VARCHAR(255)
);

LOAD DATA INFILE '/tmp/game_genres.csv' INTO TABLE GameGenreList
  FIELDS TERMINATED BY ',' ENCLOSED BY '"'
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (app_id, name);

INSERT INTO GameGenre(app_id, genre_id)
  SELECT GameGenreList.app_id, Genre.genre_id
  FROM GameGenreList
  INNER JOIN Genre ON Genre.name = GameGenreList.name;

DROP TEMPORARY TABLE GameGenreList;

DROP TEMPORARY TABLE IF EXISTS GameDeveloperList;
CREATE TEMPORARY TABLE GameDeveloperList (
  app_id INT,
  name VARCHAR(255)
);

LOAD DATA INFILE '/tmp/game_developers.csv' INTO TABLE GameDeveloperList
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' ESCAPED BY ''
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (app_id, name);

INSERT INTO GameDeveloper(app_id, developer_id)
  SELECT GameDeveloperList.app_id, Developer.developer_id
  FROM GameDeveloperList
  INNER JOIN Developer ON Developer.name = GameDeveloperList.name
  GROUP BY GameDeveloperList.app_id, Developer.developer_id;

DROP TEMPORARY TABLE GameDeveloperList;

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

# The first review_id is 0. Without this, AUTO_INCREMENT stores that 0 as 1,
# colliding with the next rows primary key. This keeps the value at 0
SET SESSION sql_mode = CONCAT(@@sql_mode, ',NO_AUTO_VALUE_ON_ZERO');
LOAD DATA INFILE '/tmp/recommendations_short_clean.csv'
  INTO TABLE SteamRecommendation
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (app_id, @helpful, @funny, recommendation_date, @is_recommended, hours_played,
   author_id, steam_recommendation_id)
  SET is_recommended = (@is_recommended = 'true');

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