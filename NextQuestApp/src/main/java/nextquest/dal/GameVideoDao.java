package nextquest.dal;

import nextquest.model.Game;
import nextquest.model.GameVideo;
import nextquest.model.VideoType;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

/**
 * DAO for the GameVideo table.
 */
public class GameVideoDao {
	protected ConnectionManager connectionManager;

	private static GameVideoDao instance = null;

	protected GameVideoDao() {
		connectionManager = new ConnectionManager();
	}

	public static GameVideoDao getInstance() {
		if (instance == null) {
			instance = new GameVideoDao();
		}
		return instance;
	}

	public GameVideo create(GameVideo gameVideo) throws SQLException {
		String insertGameVideo =
			"INSERT INTO GameVideo(app_id,name,url,video_url,video_type) " +
			"VALUES(?,?,?,?,?);";
		Connection connection = null;
		PreparedStatement insertStmt = null;
		ResultSet resultKey = null;
		try {
			connection = connectionManager.getConnection();
			insertStmt = connection.prepareStatement(insertGameVideo,
				Statement.RETURN_GENERATED_KEYS);
			insertStmt.setInt(1, gameVideo.getGame().getAppId());
			insertStmt.setString(2, gameVideo.getName());
			insertStmt.setString(3, gameVideo.getUrl());
			insertStmt.setString(4, gameVideo.getVideoUrl());
			insertStmt.setString(5, gameVideo.getVideoType().name().toLowerCase());
			insertStmt.executeUpdate();

			resultKey = insertStmt.getGeneratedKeys();
			int videoId = -1;
			if (resultKey.next()) {
				videoId = resultKey.getInt(1);
			} else {
				throw new SQLException("Unable to retrieve auto-generated key.");
			}
			gameVideo.setVideoId(videoId);
			return gameVideo;
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, insertStmt, resultKey);
		}
	}

	public GameVideo updateName(GameVideo gameVideo, String newName) throws SQLException {
		String updateGameVideo = "UPDATE GameVideo SET name=? WHERE video_id=?;";
		Connection connection = null;
		PreparedStatement updateStmt = null;
		try {
			connection = connectionManager.getConnection();
			updateStmt = connection.prepareStatement(updateGameVideo);
			updateStmt.setString(1, newName);
			updateStmt.setInt(2, gameVideo.getVideoId());
			updateStmt.executeUpdate();
			gameVideo.setName(newName);
			return gameVideo;
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, updateStmt, null);
		}
	}

	public GameVideo delete(GameVideo gameVideo) throws SQLException {
		String deleteGameVideo = "DELETE FROM GameVideo WHERE video_id=?;";
		Connection connection = null;
		PreparedStatement deleteStmt = null;
		try {
			connection = connectionManager.getConnection();
			deleteStmt = connection.prepareStatement(deleteGameVideo);
			deleteStmt.setInt(1, gameVideo.getVideoId());
			deleteStmt.executeUpdate();
			return null;
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, deleteStmt, null);
		}
	}

	public GameVideo getGameVideoById(int videoId) throws SQLException {
		String selectGameVideo =
			"SELECT video_id,app_id,name,url,video_url,video_type " +
			"FROM GameVideo WHERE video_id=?;";
		Connection connection = null;
		PreparedStatement selectStmt = null;
		ResultSet results = null;
		try {
			connection = connectionManager.getConnection();
			selectStmt = connection.prepareStatement(selectGameVideo);
			selectStmt.setInt(1, videoId);
			results = selectStmt.executeQuery();
			GameDao gameDao = GameDao.getInstance();
			if (results.next()) {
				int resultVideoId = results.getInt("video_id");
				int appId = results.getInt("app_id");
				String name = results.getString("name");
				String url = results.getString("url");
				String videoUrl = results.getString("video_url");
				VideoType videoType = VideoType.valueOf(
					results.getString("video_type").toUpperCase());

				Game game = gameDao.getGameById(appId);
				return new GameVideo(resultVideoId, game, name, url, videoUrl, videoType);
			}
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, selectStmt, results);
		}
		return null;
	}

	public List<GameVideo> getVideosByAppId(int appId) throws SQLException {
		List<GameVideo> gameVideos = new ArrayList<GameVideo>();
		String selectGameVideos =
			"SELECT video_id,app_id,name,url,video_url,video_type " +
			"FROM GameVideo WHERE app_id=?;";
		Connection connection = null;
		PreparedStatement selectStmt = null;
		ResultSet results = null;
		try {
			connection = connectionManager.getConnection();
			selectStmt = connection.prepareStatement(selectGameVideos);
			selectStmt.setInt(1, appId);
			results = selectStmt.executeQuery();
			GameDao gameDao = GameDao.getInstance();
			while (results.next()) {
				int videoId = results.getInt("video_id");
				int resultAppId = results.getInt("app_id");
				String name = results.getString("name");
				String url = results.getString("url");
				String videoUrl = results.getString("video_url");
				VideoType videoType = VideoType.valueOf(
					results.getString("video_type").toUpperCase());

				Game game = gameDao.getGameById(resultAppId);
				gameVideos.add(new GameVideo(videoId, game, name, url, videoUrl, videoType));
			}
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, selectStmt, results);
		}
		return gameVideos;
	}

	public List<GameVideo> getVideosByAppIdAndType(int appId, VideoType videoType)
			throws SQLException {
		List<GameVideo> gameVideos = new ArrayList<GameVideo>();
		String selectGameVideos =
			"SELECT video_id,app_id,name,url,video_url,video_type " +
			"FROM GameVideo WHERE app_id=? AND video_type=?;";
		Connection connection = null;
		PreparedStatement selectStmt = null;
		ResultSet results = null;
		try {
			connection = connectionManager.getConnection();
			selectStmt = connection.prepareStatement(selectGameVideos);
			selectStmt.setInt(1, appId);
			selectStmt.setString(2, videoType.name().toLowerCase());
			results = selectStmt.executeQuery();
			GameDao gameDao = GameDao.getInstance();
			while (results.next()) {
				int videoId = results.getInt("video_id");
				int resultAppId = results.getInt("app_id");
				String name = results.getString("name");
				String url = results.getString("url");
				String videoUrl = results.getString("video_url");
				VideoType resultType = VideoType.valueOf(
					results.getString("video_type").toUpperCase());

				Game game = gameDao.getGameById(resultAppId);
				gameVideos.add(new GameVideo(videoId, game, name, url, videoUrl, resultType));
			}
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, selectStmt, results);
		}
		return gameVideos;
	}

	private void close(Connection connection, PreparedStatement stmt, ResultSet results)
			throws SQLException {
		if (connection != null) {
			connection.close();
		}
		if (stmt != null) {
			stmt.close();
		}
		if (results != null) {
			results.close();
		}
	}
}
