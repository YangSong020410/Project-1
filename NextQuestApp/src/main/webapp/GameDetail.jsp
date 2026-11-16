<%@ taglib uri="http://java.sun.com/jsp/jstl/functions" prefix="fn" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/fmt" prefix="fmt" %>

<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<title>Game Detail</title>
</head>
<body>
	<h1>Game Detail</h1>
	<p><a href="genres">Manage Genres</a></p>
	<p><span style="color:red"><b>${messages.error}</b></span></p>

	<form action="gamedetail" method="get">
		<label for="appId">appId</label>
		<input id="appId" name="appId" value="${fn:escapeXml(param.appId)}">
		<input type="submit" value="Load Game">
	</form>
	<br/>

	<c:if test="${not empty game}">
		<h2><c:out value="${game.name}"/> (app_id=${game.appId})</h2>
		<p>Release date: <fmt:formatDate value="${game.releaseDate}" pattern="yyyy-MM-dd"/></p>
		<p>Price: $<c:out value="${game.price}"/></p>
		<c:if test="${not empty game.headerImage}">
			<img src="${fn:escapeXml(game.headerImage)}" width="460" alt="header"/>
		</c:if>
		<p>Metacritic: <c:out value="${game.metacriticScore}"/></p>
		<p>Positive ratings: <c:out value="${game.positiveRatings}"/>;
		   negative ratings: <c:out value="${game.negativeRatings}"/></p>
		<p>Platforms:
			<c:if test="${game.windows}">Windows </c:if>
			<c:if test="${game.mac}">Mac </c:if>
			<c:if test="${game.linux}">Linux </c:if>
		</p>
		<p>
			<a href="videocreate">Add a GameVideo</a>
		</p>

		<h3>Trailers</h3>
		<c:choose>
			<c:when test="${empty trailers}">
				<p>No trailers.</p>
			</c:when>
			<c:otherwise>
				<ul>
					<c:forEach var="v" items="${trailers}">
						<li>
							<c:out value="${v.name}"/>
							<a href="gamedetail?appId=${game.appId}&videoId=${v.videoId}">Play</a>
							| <a href="videoupdate?videoId=${v.videoId}">Update</a>
							| <a href="videodelete?videoId=${v.videoId}">Delete</a>
						</li>
					</c:forEach>
				</ul>
			</c:otherwise>
		</c:choose>

		<h3>Screenshots</h3>
		<c:choose>
			<c:when test="${empty screenshots}">
				<p>No screenshots.</p>
			</c:when>
			<c:otherwise>
				<c:forEach var="s" items="${screenshots}">
					<c:if test="${not empty s.url}">
						<img src="${fn:escapeXml(s.url)}" width="460" alt="${fn:escapeXml(s.name)}"/>
						<p><c:out value="${s.name}"/></p>
					</c:if>
				</c:forEach>
			</c:otherwise>
		</c:choose>

		<h3>Watch Trailer (HLS)</h3>
		<c:choose>
			<c:when test="${not empty selectedVideo and not empty selectedVideo.videoUrl}">
				<p><b><c:out value="${selectedVideo.name}"/></b></p>
				<video id="video" controls width="800"></video>
				<script src="https://cdn.jsdelivr.net/npm/hls.js@1"></script>
				<script>
					var video = document.getElementById('video');
					var videoSrc = "${fn:escapeXml(selectedVideo.videoUrl)}";
					if (Hls.isSupported()) {
						var hls = new Hls();
						hls.loadSource(videoSrc);
						hls.attachMedia(video);
					} else if (video.canPlayType('application/vnd.apple.mpegurl')) {
						video.src = videoSrc;
					}
				</script>
			</c:when>
			<c:otherwise>
				<p>No playable trailer video_url found for this game.</p>
			</c:otherwise>
		</c:choose>
	</c:if>
</body>
</html>
