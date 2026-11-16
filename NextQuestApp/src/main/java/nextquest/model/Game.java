package nextquest.model;

import java.math.BigDecimal;
import java.util.Date;

/**
 * Model for the Game table.
 */
public class Game {
	protected int appId;
	protected String name;
	protected Date releaseDate;
	protected BigDecimal price;
	protected String headerImage;
	protected Integer metacriticScore;
	protected Integer positiveRatings;
	protected Integer negativeRatings;
	protected Boolean windows;
	protected Boolean mac;
	protected Boolean linux;

	public Game(int appId, String name, Date releaseDate, BigDecimal price,
			String headerImage, Integer metacriticScore, Integer positiveRatings,
			Integer negativeRatings, Boolean windows, Boolean mac, Boolean linux) {
		this.appId = appId;
		this.name = name;
		this.releaseDate = releaseDate;
		this.price = price;
		this.headerImage = headerImage;
		this.metacriticScore = metacriticScore;
		this.positiveRatings = positiveRatings;
		this.negativeRatings = negativeRatings;
		this.windows = windows;
		this.mac = mac;
		this.linux = linux;
	}

	public Game(int appId) {
		this.appId = appId;
	}

	public Game(String name, Date releaseDate, BigDecimal price, String headerImage,
			Integer metacriticScore, Integer positiveRatings, Integer negativeRatings,
			Boolean windows, Boolean mac, Boolean linux) {
		this.name = name;
		this.releaseDate = releaseDate;
		this.price = price;
		this.headerImage = headerImage;
		this.metacriticScore = metacriticScore;
		this.positiveRatings = positiveRatings;
		this.negativeRatings = negativeRatings;
		this.windows = windows;
		this.mac = mac;
		this.linux = linux;
	}

	public int getAppId() {
		return appId;
	}

	public void setAppId(int appId) {
		this.appId = appId;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public Date getReleaseDate() {
		return releaseDate;
	}

	public void setReleaseDate(Date releaseDate) {
		this.releaseDate = releaseDate;
	}

	public BigDecimal getPrice() {
		return price;
	}

	public void setPrice(BigDecimal price) {
		this.price = price;
	}

	public String getHeaderImage() {
		return headerImage;
	}

	public void setHeaderImage(String headerImage) {
		this.headerImage = headerImage;
	}

	public Integer getMetacriticScore() {
		return metacriticScore;
	}

	public void setMetacriticScore(Integer metacriticScore) {
		this.metacriticScore = metacriticScore;
	}

	public Integer getPositiveRatings() {
		return positiveRatings;
	}

	public void setPositiveRatings(Integer positiveRatings) {
		this.positiveRatings = positiveRatings;
	}

	public Integer getNegativeRatings() {
		return negativeRatings;
	}

	public void setNegativeRatings(Integer negativeRatings) {
		this.negativeRatings = negativeRatings;
	}

	public Boolean getWindows() {
		return windows;
	}

	public void setWindows(Boolean windows) {
		this.windows = windows;
	}

	public Boolean getMac() {
		return mac;
	}

	public void setMac(Boolean mac) {
		this.mac = mac;
	}

	public Boolean getLinux() {
		return linux;
	}

	public void setLinux(Boolean linux) {
		this.linux = linux;
	}
}
