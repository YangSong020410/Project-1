CREATE SCHEMA IF NOT EXISTS NextQuest;
USE NextQuest;

DROP TABLE IF EXISTS RecommendationSurvey;
DROP TABLE IF EXISTS Review;
DROP TABLE IF EXISTS SavedGame;
DROP TABLE IF EXISTS GameGenre;
DROP TABLE IF EXISTS GameDeveloper;
DROP TABLE IF EXISTS GameVideo;
DROP TABLE IF EXISTS SteamReview;
DROP TABLE IF EXISTS SteamRecommendation;
DROP TABLE IF EXISTS Game;
DROP TABLE IF EXISTS User;
DROP TABLE IF EXISTS Genre;
DROP TABLE IF EXISTS Developer;

CREATE TABLE User (
  user_id INT AUTO_INCREMENT,
  username VARCHAR(255),
  email VARCHAR(255),
  CONSTRAINT pk_User_user_id PRIMARY KEY (user_id)
);

CREATE TABLE Genre (
  genre_id INT AUTO_INCREMENT,
  name VARCHAR(255),
  CONSTRAINT pk_Genre_genre_id PRIMARY KEY (genre_id)
);

CREATE TABLE Developer (
  developer_id INT AUTO_INCREMENT,
  name VARCHAR(255),
  CONSTRAINT pk_Developer_developer_id PRIMARY KEY (developer_id)
);

CREATE TABLE Game (
  app_id INT AUTO_INCREMENT,
  name VARCHAR(255),
  release_date DATE,
  price DECIMAL(10,2),
  header_image VARCHAR(255),
  metacritic_score INT,
  positive_ratings INT,
  negative_ratings INT,
  windows BOOLEAN,
  mac BOOLEAN,
  linux BOOLEAN,
  CONSTRAINT pk_Game_app_id PRIMARY KEY (app_id)
);

CREATE TABLE GameVideo (
  video_id INT AUTO_INCREMENT,
  app_id INT NOT NULL,
  name VARCHAR(255),
  url VARCHAR(255),
  video_url VARCHAR(255),
  video_type ENUM ('trailer', 'gameplay', 'screenshot') NOT NULL,
  CONSTRAINT pk_GameVideo_video_id PRIMARY KEY (video_id),
  CONSTRAINT fk_GameVideo_app_id
    FOREIGN KEY (app_id)
    REFERENCES Game(app_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE SavedGame (
  user_id INT,
  app_id INT,
  saved_at TIMESTAMP,
  CONSTRAINT pk_SavedGame_user_id_app_id PRIMARY KEY (user_id, app_id),
  CONSTRAINT fk_SavedGame_user_id
    FOREIGN KEY (user_id)
    REFERENCES User(user_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_SavedGame_app_id
    FOREIGN KEY (app_id)
    REFERENCES Game(app_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE Review (
  review_id INT AUTO_INCREMENT,
  app_id INT NOT NULL,
  user_id INT NOT NULL,
  is_recommended BOOLEAN,
  hours_played DECIMAL(10,2),
  review_date DATE,
  CONSTRAINT pk_Review_review_id PRIMARY KEY (review_id),
  CONSTRAINT uq_Review_user_id_app_id UNIQUE (user_id, app_id),
  CONSTRAINT fk_Review_app_id
    FOREIGN KEY (app_id)
    REFERENCES Game(app_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_Review_user_id
    FOREIGN KEY (user_id)
    REFERENCES User(user_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE RecommendationSurvey (
  survey_id INT AUTO_INCREMENT,
  user_id INT NOT NULL,
  preferred_genre VARCHAR(255),
  preferred_platform VARCHAR(255),
  play_style VARCHAR(255),
  updated_at TIMESTAMP,
  CONSTRAINT pk_RecommendationSurvey_survey_id PRIMARY KEY (survey_id),
  CONSTRAINT fk_RecommendationSurvey_user_id
    FOREIGN KEY (user_id)
    REFERENCES User(user_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE GameGenre (
  app_id INT,
  genre_id INT,
  CONSTRAINT pk_GameGenre_app_id_genre_id PRIMARY KEY (app_id, genre_id),
  CONSTRAINT fk_GameGenre_app_id
    FOREIGN KEY (app_id)
    REFERENCES Game(app_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_GameGenre_genre_id
    FOREIGN KEY (genre_id)
    REFERENCES Genre(genre_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE GameDeveloper (
  app_id INT,
  developer_id INT,
  CONSTRAINT pk_GameDeveloper_app_id_developer_id PRIMARY KEY (app_id, developer_id),
  CONSTRAINT fk_GameDeveloper_app_id
    FOREIGN KEY (app_id)
    REFERENCES Game(app_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_GameDeveloper_developer_id
    FOREIGN KEY (developer_id)
    REFERENCES Developer(developer_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE SteamRecommendation (
  steam_recommendation_id INT AUTO_INCREMENT,
  app_id INT NOT NULL,
  author_id INT,
  is_recommended BOOLEAN,
  hours_played DECIMAL(10,2),
  recommendation_date DATE,
  CONSTRAINT pk_SteamRecommendation_steam_recommendation_id PRIMARY KEY (steam_recommendation_id),
  CONSTRAINT fk_SteamRecommendation_app_id
    FOREIGN KEY (app_id)
    REFERENCES Game(app_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE SteamReview (
  steam_review_id INT AUTO_INCREMENT,
  app_id INT NOT NULL,
  author_steamid BIGINT,
  is_recommended BOOLEAN,
  hours_played DECIMAL(10,2),
  review_date DATE,
  language VARCHAR(255),
  CONSTRAINT pk_SteamReview_steam_review_id PRIMARY KEY (steam_review_id),
  CONSTRAINT fk_SteamReview_app_id
    FOREIGN KEY (app_id)
    REFERENCES Game(app_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);