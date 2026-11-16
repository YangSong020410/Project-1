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
 * Genre delete page.
 */
@WebServlet("/genredelete")
public class GenreDelete extends HttpServlet {

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

		req.getRequestDispatcher("/GenreDelete.jsp").forward(req, resp);
	}

	@Override
	public void doPost(HttpServletRequest req, HttpServletResponse resp)
			throws ServletException, IOException {
		Map<String, String> messages = new HashMap<String, String>();
		req.setAttribute("messages", messages);

		String genreIdParam = req.getParameter("genreId");
		if (genreIdParam == null || genreIdParam.trim().isEmpty()) {
			messages.put("error", "Please provide a genreId.");
		} else {
			try {
				int genreId = Integer.parseInt(genreIdParam);
				Genre genre = genreDao.getGenreById(genreId);
				if (genre == null) {
					messages.put("error", "Genre not found.");
				} else {
					genreDao.delete(genre);
					messages.put("success", "Deleted genre id=" + genreId);
				}
			} catch (NumberFormatException e) {
				messages.put("error", "genreId must be a number.");
			} catch (SQLException e) {
				e.printStackTrace();
				throw new IOException(e);
			}
		}

		req.getRequestDispatcher("/GenreDelete.jsp").forward(req, resp);
	}
}
