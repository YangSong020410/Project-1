-- 把 Steam 视频链接回填进 GameVideo.video_url（只补链接，不删不改现有数据）。
-- 跑之前：cp video_links.csv /tmp/video_links.csv
-- 注意：第一次跑 ALTER 时如果报 Duplicate column，说明列已存在，忽略该报错继续往下跑。
USE NextQuest;

-- 1. 加 video_url 列（缩略图继续存在 url 里，视频链接单独一列）
ALTER TABLE GameVideo ADD COLUMN video_url VARCHAR(255) NULL AFTER url;

-- 2. 暂存表装脚本抓到的视频链接
DROP TEMPORARY TABLE IF EXISTS VideoLinkStaging;
CREATE TEMPORARY TABLE VideoLinkStaging (
  app_id INT,
  movie_id VARCHAR(32),
  name VARCHAR(255),
  mp4_url VARCHAR(255),
  webm_url VARCHAR(255)
);

LOAD DATA INFILE '/tmp/video_links.csv'
  INTO TABLE VideoLinkStaging
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (app_id, movie_id, name, mp4_url, webm_url);

-- 3. 回填：优先按缩略图链接里的 movie id 匹配，名字作兜底；mp4 优先，webm 兜底
UPDATE GameVideo v
INNER JOIN VideoLinkStaging s
  ON s.app_id = v.app_id
  AND v.video_type = 'trailer'
  AND (v.url LIKE CONCAT('%/', s.movie_id, '/%') OR v.name = s.name)
SET v.video_url = COALESCE(NULLIF(s.mp4_url, ''), NULLIF(s.webm_url, ''));

SELECT ROW_COUNT() AS updated_rows;

-- 4. 核对
SELECT COUNT(*) AS trailers_total FROM GameVideo WHERE video_type = 'trailer';
SELECT COUNT(*) AS trailers_with_video FROM GameVideo WHERE video_type = 'trailer' AND video_url IS NOT NULL;
SELECT COUNT(*) AS trailers_without_video FROM GameVideo WHERE video_type = 'trailer' AND video_url IS NULL;

DROP TEMPORARY TABLE VideoLinkStaging;
