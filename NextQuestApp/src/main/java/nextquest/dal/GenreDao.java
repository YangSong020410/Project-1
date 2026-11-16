package nextquest.dal;

import nextquest.model.Genre;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

/**
 * DAO for the Genre table.
 */
public class GenreDao {
	protected ConnectionManager connectionManager;

	private static GenreDao instance = null;

	protected GenreDao() {
		connectionManager = new ConnectionManager();
	}

	public static GenreDao getInstance() {
		if (instance == null) {
			instance = new GenreDao();
		}
		return instance;
	}

	public Genre create(Genre genre) throws SQLException {
		String insertGenre = "INSERT INTO Genre(name) VALUES(?);";
		Connection connection = null;
		PreparedStatement insertStmt = null;
		ResultSet resultKey = null;
		try {
			connection = connectionManager.getConnection();
			insertStmt = connection.prepareStatement(insertGenre,
				Statement.RETURN_GENERATED_KEYS);
			insertStmt.setString(1, genre.getName());
			insertStmt.executeUpdate();

			resultKey = insertStmt.getGeneratedKeys();
			int genreId = -1;
			if (resultKey.next()) {
				genreId = resultKey.getInt(1);
			} else {
				throw new SQLException("Unable to retrieve auto-generated key.");
			}
			genre.setGenreId(genreId);
			return genre;
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, insertStmt, resultKey);
		}
	}

	public Genre updateName(Genre genre, String newName) throws SQLException {
		String updateGenre = "UPDATE Genre SET name=? WHERE genre_id=?;";
		Connection connection = null;
		PreparedStatement updateStmt = null;
		try {
			connection = connectionManager.getConnection();
			updateStmt = connection.prepareStatement(updateGenre);
			updateStmt.setString(1, newName);
			updateStmt.setInt(2, genre.getGenreId());
			updateStmt.executeUpdate();
			genre.setName(newName);
			return genre;
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, updateStmt, null);
		}
	}

	public Genre delete(Genre genre) throws SQLException {
		String deleteGenre = "DELETE FROM Genre WHERE genre_id=?;";
		Connection connection = null;
		PreparedStatement deleteStmt = null;
		try {
			connection = connectionManager.getConnection();
			deleteStmt = connection.prepareStatement(deleteGenre);
			deleteStmt.setInt(1, genre.getGenreId());
			deleteStmt.executeUpdate();
			return null;
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, deleteStmt, null);
		}
	}

	public Genre getGenreById(int genreId) throws SQLException {
		String selectGenre = "SELECT genre_id,name FROM Genre WHERE genre_id=?;";
		Connection connection = null;
		PreparedStatement selectStmt = null;
		ResultSet results = null;
		try {
			connection = connectionManager.getConnection();
			selectStmt = connection.prepareStatement(selectGenre);
			selectStmt.setInt(1, genreId);
			results = selectStmt.executeQuery();
			if (results.next()) {
				int resultId = results.getInt("genre_id");
				String name = results.getString("name");
				return new Genre(resultId, name);
			}
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, selectStmt, results);
		}
		return null;
	}

	public List<Genre> getAllGenres() throws SQLException {
		List<Genre> genres = new ArrayList<Genre>();
		String selectGenres = "SELECT genre_id,name FROM Genre ORDER BY name;";
		Connection connection = null;
		PreparedStatement selectStmt = null;
		ResultSet results = null;
		try {
			connection = connectionManager.getConnection();
			selectStmt = connection.prepareStatement(selectGenres);
			results = selectStmt.executeQuery();
			while (results.next()) {
				int genreId = results.getInt("genre_id");
				String resultName = results.getString("name");
				genres.add(new Genre(genreId, resultName));
			}
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, selectStmt, results);
		}
		return genres;
	}

	public List<Genre> getGenresByName(String name) throws SQLException {
		List<Genre> genres = new ArrayList<Genre>();
		String selectGenres = "SELECT genre_id,name FROM Genre WHERE name=?;";
		Connection connection = null;
		PreparedStatement selectStmt = null;
		ResultSet results = null;
		try {
			connection = connectionManager.getConnection();
			selectStmt = connection.prepareStatement(selectGenres);
			selectStmt.setString(1, name);
			results = selectStmt.executeQuery();
			while (results.next()) {
				int genreId = results.getInt("genre_id");
				String resultName = results.getString("name");
				genres.add(new Genre(genreId, resultName));
			}
		} catch (SQLException e) {
			e.printStackTrace();
			throw e;
		} finally {
			close(connection, selectStmt, results);
		}
		return genres;
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
