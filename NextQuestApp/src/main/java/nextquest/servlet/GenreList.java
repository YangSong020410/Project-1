package nextquest.servlet;

import nextquest.dal.GenreDao;
import nextquest.model.Genre;

import java.io.IOException;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * Genre list page. GET renders the list; POST creates a new Genre.
 */
@WebServlet("/genres")
public class GenreList extends HttpServlet {

	protected GenreDao genreDao;

	@Override
	public void init() throws ServletException {
		genreDao = GenreDao.getInstance();
	}

	@Override
	public void doGet(HttpServletRequest req, HttpServletResponse resp)
			throws ServletException, IOException {
		Map<String, String> messages = new HashMap<String, String>();
		req.setAttribute("messages", messages);

		try {
			List<Genre> genres = genreDao.getAllGenres();
			req.setAttribute("genres", genres);
		} catch (SQLException e) {
			e.printStackTrace();
			throw new IOException(e);
		}

		req.getRequestDispatcher("/GenreList.jsp").forward(req, resp);
	}

	@Override
	public void doPost(HttpServletRequest req, HttpServletResponse resp)
			throws ServletException, IOException {
		Map<String, String> messages = new HashMap<String, String>();
		req.setAttribute("messages", messages);

		String name = req.getParameter("name");
		if (name == null || name.trim().isEmpty()) {
			messages.put("error", "Genre name is required.");
		} else {
			try {
				Genre genre = new Genre(name.trim());
				genre = genreDao.create(genre);
				messages.put("success", "Created genre id=" + genre.getGenreId());
			} catch (SQLException e) {
				e.printStackTrace();
				throw new IOException(e);
			}
		}

		// Re-render the list.
		try {
			List<Genre> genres = genreDao.getAllGenres();
			req.setAttribute("genres", genres);
		} catch (SQLException e) {
			e.printStackTrace();
			throw new IOException(e);
		}
		req.getRequestDispatcher("/GenreList.jsp").forward(req, resp);
	}
}
