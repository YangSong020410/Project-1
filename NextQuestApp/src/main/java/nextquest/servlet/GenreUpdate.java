package nextquest.servlet;

import nextquest.dal.GenreDao;
import nextquest.model.Genre;

import java.io.IOException;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.Map;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * Genre update page.
 */
@WebServlet("/genreupdate")
public class GenreUpdate extends HttpServlet {

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

		String genreIdParam = req.getParameter("genreId");
		if (genreIdParam == null || genreIdParam.trim().isEmpty()) {
			messages.put("error", "Please provide a genreId.");
		} else {
			try {
				Genre genre = genreDao.getGenreById(Integer.parseInt(genreIdParam));
				req.setAttribute("genre", genre);
			} catch (NumberFormatException e) {
				messages.put("error", "genreId must be a number.");
			} catch (SQLException e) {
				e.printStackTrace();
				throw new IOException(e);
			}
		}

		req.getRequestDispatcher("/GenreUpdate.jsp").forward(req, resp);
	}

	@Override
	public void doPost(HttpServletRequest req, HttpServletResponse resp)
			throws ServletException, IOException {
		Map<String, String> messages = new HashMap<String, String>();
		req.setAttribute("messages", messages);

		String genreIdParam = req.getParameter("genreId");
		String name = req.getParameter("name");
		if (genreIdParam == null || genreIdParam.trim().isEmpty()) {
			messages.put("error", "Please provide a genreId.");
		} else if (name == null || name.trim().isEmpty()) {
			messages.put("error", "Genre name is required.");
		} else {
			try {
				int genreId = Integer.parseInt(genreIdParam);
				Genre genre = genreDao.getGenreById(genreId);
				if (genre == null) {
					messages.put("error", "Genre not found.");
				} else {
					genre = genreDao.updateName(genre, name.trim());
					messages.put("success", "Updated genre id=" + genre.getGenreId());
					req.setAttribute("genre", genre);
				}
			} catch (NumberFormatException e) {
				messages.put("error", "genreId must be a number.");
			} catch (SQLException e) {
				e.printStackTrace();
				throw new IOException(e);
			}
		}

		req.getRequestDispatcher("/GenreUpdate.jsp").forward(req, resp);
	}
}
