package nextquest.model;

/**
 * Model for the GameVideo table.
 * The app_id foreign key is held as a Game object reference.
 */
public class GameVideo {
	protected int videoId;
	protected Game game;
	protected String name;
	protected String url;
	protected String videoUrl;
	protected VideoType videoType;

	public GameVideo(int videoId, Game game, String name, String url,
			String videoUrl, VideoType videoType) {
		this.videoId = videoId;
		this.game = game;
		this.name = name;
		this.url = url;
		this.videoUrl = videoUrl;
		this.videoType = videoType;
	}

	public GameVideo(int videoId) {
		this.videoId = videoId;
	}

	public GameVideo(Game game, String name, String url, String videoUrl,
			VideoType videoType) {
		this.game = game;
		this.name = name;
		this.url = url;
		this.videoUrl = videoUrl;
		this.videoType = videoType;
	}

	public int getVideoId() {
		return videoId;
	}

	public void setVideoId(int videoId) {
		this.videoId = videoId;
	}

	public Game getGame() {
		return game;
	}

	public void setGame(Game game) {
		this.game = game;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public String getUrl() {
		return url;
	}

	public void setUrl(String url) {
		this.url = url;
	}

	public String getVideoUrl() {
		return videoUrl;
	}

	public void setVideoUrl(String videoUrl) {
		this.videoUrl = videoUrl;
	}

	public VideoType getVideoType() {
		return videoType;
	}

	public void setVideoType(VideoType videoType) {
		this.videoType = videoType;
	}
}
