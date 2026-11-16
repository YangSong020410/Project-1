package nextquest.servlet;

import nextquest.dal.GameVideoDao;
import nextquest.model.GameVideo;

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
 * GameVideo update page.
 */
@WebServlet("/videoupdate")
public class GameVideoUpdate extends HttpServlet {

	protected GameVideoDao gameVideoDao;

	@Override
	public void init() throws ServletException {
		gameVideoDao = GameVideoDao.getInstance();
	}

	@Override
	public void doGet(HttpServletRequest req, HttpServletResponse resp)
			throws ServletException, IOException {
		Map<String, String> messages = new HashMap<String, String>();
		req.setAttribute("messages", messages);

		String videoIdParam = req.getParameter("videoId");
		if (videoIdParam == null || videoIdParam.trim().isEmpty()) {
			messages.put("error", "Please provide a videoId.");
		} else {
			try {
				GameVideo gameVideo = gameVideoDao.getGameVideoById(
					Integer.parseInt(videoIdParam));
				req.setAttribute("gameVideo", gameVideo);
			} catch (NumberFormatException e) {
				messages.put("error", "videoId must be a number.");
			} catch (SQLException e) {
				e.printStackTrace();
				throw new IOException(e);
			}
		}

		req.getRequestDispatcher("/GameVideoUpdate.jsp").forward(req, resp);
	}

	@Override
	public void doPost(HttpServletRequest req, HttpServletResponse resp)
			throws ServletException, IOException {
		Map<String, String> messages = new HashMap<String, String>();
		req.setAttribute("messages", messages);

		String videoIdParam = req.getParameter("videoId");
		String name = req.getParameter("name");
		if (videoIdParam == null || videoIdParam.trim().isEmpty()) {
			messages.put("error", "Please provide a videoId.");
		} else if (name == null || name.trim().isEmpty()) {
			messages.put("error", "Name is required.");
		} else {
			try {
				int videoId = Integer.parseInt(videoIdParam);
				GameVideo gameVideo = gameVideoDao.getGameVideoById(videoId);
				if (gameVideo == null) {
					messages.put("error", "GameVideo not found.");
				} else {
					gameVideo = gameVideoDao.updateName(gameVideo, name.trim());
					messages.put("success", "Updated video id=" + gameVideo.getVideoId());
					req.setAttribute("gameVideo", gameVideo);
				}
			} catch (NumberFormatException e) {
				messages.put("error", "videoId must be a number.");
			} catch (SQLException e) {
				e.printStackTrace();
				throw new IOException(e);
			}
		}

		req.getRequestDispatcher("/GameVideoUpdate.jsp").forward(req, resp);
	}
}
