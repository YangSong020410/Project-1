USE NextQuest;
DELETE FROM SteamReview;
DELETE FROM SteamRecommendation;
DELETE FROM Game;
/**
Data Setup:
Copy the three CSV files onto your computer. The names must match

Mac terminal commands for a smooth transfer (replace "downloads" with you csv file location):

cp ~/Downloads/games_short.csv /tmp/games_short.csv
cp ~/Downloads/all_reviews_short.csv /tmp/all_reviews_short.csv
cp ~/Downloads/recommendations_short.csv /tmp/recommendations_short.csv

*/
SET GLOBAL local_infile = 1;
LOAD DATA INFILE '/tmp/games_short.csv'
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

LOAD DATA INFILE '/tmp/all_reviews_short.csv'
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
LOAD DATA INFILE '/tmp/recommendations_short.csv'
  INTO TABLE SteamRecommendation
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (app_id, @helpful, @funny, recommendation_date, @is_recommended, hours_played,
   author_id, steam_recommendation_id)
  SET is_recommended = (@is_recommended = 'true');

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