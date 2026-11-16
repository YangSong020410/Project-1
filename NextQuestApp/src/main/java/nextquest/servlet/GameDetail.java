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
 * Game detail page. Shows one game plus its trailers/screenshots and
 * an embedded HLS player (advanced feature) for the selected trailer.
 */
@WebServlet("/gamedetail")
public class GameDetail extends HttpServlet {

	protected GameDao gameDao;
	protected GameVideoDao gameVideoDao;

	@Override
	public void init() throws ServletException {
		gameDao = GameDao.getInstance();
		gameVideoDao = GameVideoDao.getInstance();
	}

	@Override
	public void doGet(HttpServletRequest req, HttpServletResponse resp)
			throws ServletException, IOException {
		Map<String, String> messages = new HashMap<String, String>();
		req.setAttribute("messages", messages);

		String appIdParam = req.getParameter("appId");
		if (appIdParam == null || appIdParam.trim().isEmpty()) {
			messages.put("error", "Please provide an appId.");
			req.getRequestDispatcher("/GameDetail.jsp").forward(req, resp);
			return;
		}

		try {
			int appId = Integer.parseInt(appIdParam);
			Game game = gameDao.getGameById(appId);
			req.setAttribute("game", game);

			if (game != null) {
				List<GameVideo> trailers = gameVideoDao.getVideosByAppIdAndType(
					appId, VideoType.TRAILER);
				List<GameVideo> screenshots = gameVideoDao.getVideosByAppIdAndType(
					appId, VideoType.SCREENSHOT);
				req.setAttribute("trailers", trailers);
				req.setAttribute("screenshots", screenshots);

				// Select the trailer to play: ?videoId= overrides, otherwise
				// the first trailer with a non-null video_url.
				String selectedParam = req.getParameter("videoId");
				GameVideo selected = null;
				if (selectedParam != null && !selectedParam.trim().isEmpty()) {
					int selectedId = Integer.parseInt(selectedParam);
					selected = gameVideoDao.getGameVideoById(selectedId);
				}
				if (selected == null) {
					for (GameVideo t : trailers) {
						if (t.getVideoUrl() != null && !t.getVideoUrl().isEmpty()) {
							selected = t;
							break;
						}
					}
				}
				req.setAttribute("selectedVideo", selected);
			}
		} catch (NumberFormatException e) {
			messages.put("error", "appId must be a number.");
		} catch (SQLException e) {
			e.printStackTrace();
			throw new IOException(e);
		}

		req.getRequestDispatcher("/GameDetail.jsp").forward(req, resp);
	}
}
