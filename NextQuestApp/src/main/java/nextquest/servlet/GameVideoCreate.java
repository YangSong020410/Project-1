package nextquest.servlet;

import nextquest.dal.GameDao;
import nextquest.dal.GameVideoDao;
import nextquest.model.Game;
import nextquest.model.GameVideo;
import nextquest.model.VideoType;

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
 * GameVideo create page. Loads all games for the app_id dropdown.
 */
@WebServlet("/videocreate")
public class GameVideoCreate extends HttpServlet {

	protected GameVideoDao gameVideoDao;
	protected GameDao gameDao;

	@Override
	public void init() throws ServletException {
		gameVideoDao = GameVideoDao.getInstance();
		gameDao = GameDao.getInstance();
	}

	@Override
	public void doGet(HttpServletRequest req, HttpServletResponse resp)
			throws ServletException, IOException {
		Map<String, String> messages = new HashMap<String, String>();
		req.setAttribute("messages", messages);
		req.getRequestDispatcher("/GameVideoCreate.jsp").forward(req, resp);
	}

	@Override
	public void doPost(HttpServletRequest req, HttpServletResponse resp)
			throws ServletException, IOException {
		Map<String, String> messages = new HashMap<String, String>();
		req.setAttribute("messages", messages);

		String appIdParam = req.getParameter("appId");
		String name = req.getParameter("name");
		String url = req.getParameter("url");
		String videoUrl = req.getParameter("videoUrl");
		String videoTypeParam = req.getParameter("videoType");

		if (appIdParam == null || appIdParam.trim().isEmpty()) {
			messages.put("error", "appId is required.");
		} else if (videoTypeParam == null || videoTypeParam.trim().isEmpty()) {
			messages.put("error", "videoType is required.");
		} else {
			try {
				int appId = Integer.parseInt(appIdParam);
				Game game = gameDao.getGameById(appId);
				if (game == null) {
					messages.put("error", "Game not found.");
				} else {
					VideoType videoType = VideoType.valueOf(
						videoTypeParam.trim().toUpperCase());
					GameVideo gameVideo = new GameVideo(game, name, url, videoUrl, videoType);
					gameVideo = gameVideoDao.create(gameVideo);
					messages.put("success", "Created video id=" + gameVideo.getVideoId());
				}
			} catch (NumberFormatException e) {
				messages.put("error", "appId must be a number.");
			} catch (IllegalArgumentException e) {
				messages.put("error", "videoType must be trailer, gameplay, or screenshot.");
			} catch (SQLException e) {
				e.printStackTrace();
				throw new IOException(e);
			}
		}

		req.getRequestDispatcher("/GameVideoCreate.jsp").forward(req, resp);
	}
}
