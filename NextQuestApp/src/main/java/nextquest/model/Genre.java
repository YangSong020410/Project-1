package nextquest.model;

/**
 * Model for the Genre table.
 */
public class Genre {
	protected int genreId;
	protected String name;

	public Genre(int genreId, String name) {
		this.genreId = genreId;
		this.name = name;
	}

	public Genre(int genreId) {
		this.genreId = genreId;
	}

	public Genre(String name) {
		this.name = name;
	}

	public int getGenreId() {
		return genreId;
	}

	public void setGenreId(int genreId) {
		this.genreId = genreId;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}
}
