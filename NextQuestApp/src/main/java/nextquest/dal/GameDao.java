package nextquest.dal;

import nextquest.model.Game;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

/**
 * DAO for the Game table.
 */
public class GameDao {
	protected ConnectionManager connectionManager;

	private static GameDao instance = null;

	protected GameDao() {
		connectionManager = new ConnectionManager();
	}

	public static GameDao getInstance() {
		if (instance == null) {
			instance = new GameDao();
		}
		return instance;
	}

	public Game create(Game game) throws SQLException {
		String insertGame =
			"INSERT INTO Game(name,release_date,price,header_image,metacritic_score," +
			"positive_ratings,negative_ratings,windows,mac,linux) " +
			"VALUES(?,?,?,?,?,?,?,?,?,?);";
		Connection connection = null;
		PreparedStatement insertStmt = null;
		ResultSet resultKey = null;
		try {
			connection = connectionManager.getConnection();
			insertStmt = connection.prepareStatement(insertGame,
				Statement.RETURN_GENERATED_KEYS);
			insertStmt.setString(1, game.getName());
			insertStmt.setDate(2, game.getReleaseDate() == null ? null :
				new Date(game.getReleaseDate().getTime()));
			insertStmt.setBigDecimal(3, game.getPrice());
			insertStmt.setString(4, game.getHeaderImage());
			setNullableInt(insertStmt, 5, game.getMetacriticScore());
			setNullableInt(insertStmt, 6, game.getPositiveRatings());
			setNullableInt(insertStmt, 7, game.getNegativeRatings());
			setNullableBoolean(insertStmt, 8, game.getWindows());
			setNullableBoolean(insertStmt, 9, game.getMac());
			setNullableBoolean(insertStmt, 10, game.getLinux());
			insertStmt.executeUpdate();

			resultKey = insertStmt.getGeneratedKeys();
			int appId = -1;
			if (resultKey.next()) {
				appId = resultKey.getInt(1);
			} else {
				throw new SQLException("Unable to retrieve auto-generated key.");
			}
			game.setAppId(appId);
			return game;
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, insertStmt, resultKey);
		}
	}

	public Game updateName(Game game, String newName) throws SQLException {
		String updateGame = "UPDATE Game SET name=? WHERE app_id=?;";
		Connection connection = null;
		PreparedStatement updateStmt = null;
		try {
			connection = connectionManager.getConnection();
			updateStmt = connection.prepareStatement(updateGame);
			updateStmt.setString(1, newName);
			updateStmt.setInt(2, game.getAppId());
			updateStmt.executeUpdate();
			game.setName(newName);
			return game;
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, updateStmt, null);
		}
	}

	public Game delete(Game game) throws SQLException {
		String deleteGame = "DELETE FROM Game WHERE app_id=?;";
		Connection connection = null;
		PreparedStatement deleteStmt = null;
		try {
			connection = connectionManager.getConnection();
			deleteStmt = connection.prepareStatement(deleteGame);
			deleteStmt.setInt(1, game.getAppId());
			deleteStmt.executeUpdate();
			return null;
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, deleteStmt, null);
		}
	}

	public Game getGameById(int appId) throws SQLException {
		String selectGame =
			"SELECT app_id,name,release_date,price,header_image,metacritic_score," +
			"positive_ratings,negative_ratings,windows,mac,linux " +
			"FROM Game WHERE app_id=?;";
		Connection connection = null;
		PreparedStatement selectStmt = null;
		ResultSet results = null;
		try {
			connection = connectionManager.getConnection();
			selectStmt = connection.prepareStatement(selectGame);
			selectStmt.setInt(1, appId);
			results = selectStmt.executeQuery();
			if (results.next()) {
				return extractGame(results);
			}
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, selectStmt, results);
		}
		return null;
	}

	private Game extractGame(ResultSet results) throws SQLException {
		int appId = results.getInt("app_id");
		String name = results.getString("name");
		java.util.Date releaseDate = results.getDate("release_date");
		BigDecimal price = results.getBigDecimal("price");
		String headerImage = results.getString("header_image");
		Integer metacriticScore = results.getInt("metacritic_score");
		if (results.wasNull()) {
			metacriticScore = null;
		}
		Integer positiveRatings = results.getInt("positive_ratings");
		if (results.wasNull()) {
			positiveRatings = null;
		}
		Integer negativeRatings = results.getInt("negative_ratings");
		if (results.wasNull()) {
			negativeRatings = null;
		}
		Boolean windows = results.getBoolean("windows");
		if (results.wasNull()) {
			windows = null;
		}
		Boolean mac = results.getBoolean("mac");
		if (results.wasNull()) {
			mac = null;
		}
		Boolean linux = results.getBoolean("linux");
		if (results.wasNull()) {
			linux = null;
		}
		return new Game(appId, name, releaseDate, price, headerImage,
			metacriticScore, positiveRatings, negativeRatings, windows, mac, linux);
	}

	private void setNullableInt(PreparedStatement stmt, int index, Integer value)
			throws SQLException {
		if (value == null) {
			stmt.setNull(index, java.sql.Types.INTEGER);
		} else {
			stmt.setInt(index, value);
		}
	}

	private void setNullableBoolean(PreparedStatement stmt, int index, Boolean value)
			throws SQLException {
		if (value == null) {
			stmt.setNull(index, java.sql.Types.BOOLEAN);
		} else {
			stmt.setBoolean(index, value);
		}
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
