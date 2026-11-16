package nextquest.tools;

import nextquest.dal.GameDao;
import nextquest.dal.GameVideoDao;
import nextquest.dal.GenreDao;
import nextquest.model.Game;
import nextquest.model.GameVideo;
import nextquest.model.Genre;
import nextquest.model.VideoType;

import java.math.BigDecimal;
import java.sql.SQLException;
import java.util.Date;
import java.util.List;

/**
 * main() runner to exercise CRUD on Game, Genre, and GameVideo.
 * Run it, verify the output, then delete the test rows it created
 * (the last block already removes them so the DB stays clean).
 */
public class Inserter {

	public static void main(String[] args) throws SQLException {
		GameDao gameDao = GameDao.getInstance();
		GenreDao genreDao = GenreDao.getInstance();
		GameVideoDao gameVideoDao = GameVideoDao.getInstance();

		// CREATE / READ / UPDATE / DELETE a Genre.
		Genre genre = new Genre("TestGenre");
		genre = genreDao.create(genre);
		System.out.format("Created genre: id=%d name=%s%n",
			genre.getGenreId(), genre.getName());

		Genre readGenre = genreDao.getGenreById(genre.getGenreId());
		System.out.format("Read genre: id=%d name=%s%n",
			readGenre.getGenreId(), readGenre.getName());

		genre = genreDao.updateName(genre, "TestGenreUpdated");
		System.out.format("Updated genre: id=%d name=%s%n",
			genre.getGenreId(), genre.getName());

		genreDao.delete(genre);
		System.out.format("Deleted genre id=%d%n", genre.getGenreId());

		// CREATE / READ a Game.
		Game game = new Game("TestGame", new Date(), new BigDecimal("9.99"),
			null, 80, 100, 5, true, false, false);
		game = gameDao.create(game);
		System.out.format("Created game: app_id=%d name=%s%n",
			game.getAppId(), game.getName());

		Game readGame = gameDao.getGameById(game.getAppId());
		System.out.format("Read game: app_id=%d name=%s price=%s%n",
			readGame.getAppId(), readGame.getName(), readGame.getPrice());

		// CREATE / READ a GameVideo (trailer).
		GameVideo video = new GameVideo(game, "TestTrailer", null,
			"https://example.com/trailer.m3u8", VideoType.TRAILER);
		video = gameVideoDao.create(video);
		System.out.format("Created video: video_id=%d app_id=%d type=%s%n",
			video.getVideoId(), video.getGame().getAppId(), video.getVideoType());

		GameVideo readVideo = gameVideoDao.getGameVideoById(video.getVideoId());
		System.out.format("Read video: video_id=%d name=%s video_url=%s%n",
			readVideo.getVideoId(), readVideo.getName(), readVideo.getVideoUrl());

		// UPDATE video name.
		video = gameVideoDao.updateName(video, "TestTrailerUpdated");
		System.out.format("Updated video name=%s%n", video.getName());

		// READ videos by app_id and type.
		List<GameVideo> trailers = gameVideoDao.getVideosByAppIdAndType(
			game.getAppId(), VideoType.TRAILER);
		System.out.format("Trailers for app_id=%d: %d%n", game.getAppId(), trailers.size());

		// Clean up: delete video then game.
		gameVideoDao.delete(video);
		gameDao.delete(game);
		System.out.println("Cleaned up test GameVideo and Game.");
	}
}
