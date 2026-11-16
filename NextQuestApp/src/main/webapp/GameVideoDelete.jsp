<%@ taglib uri="http://java.sun.com/jsp/jstl/functions" prefix="fn" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/fmt" prefix="fmt" %>

<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<title>Delete GameVideo</title>
</head>
<body>
	<h1>Delete GameVideo</h1>
	<p><a href="gamedetail">Back to Game Detail</a></p>
	<p><span style="color:green"><b>${messages.success}</b></span></p>
	<p><span style="color:red"><b>${messages.error}</b></span></p>

	<form action="videodelete" method="get">
		<label for="videoId">videoId</label>
		<input id="videoId" name="videoId" value="${fn:escapeXml(param.videoId)}">
		<input type="submit" value="Load">
	</form>
	<br/>

	<c:if test="${not empty gameVideo}">
		<p>Are you sure you want to delete video_id=${gameVideo.videoId}, name=<c:out value="${gameVideo.name}"/>?</p>
		<form action="videodelete" method="post">
			<input type="hidden" name="videoId" value="${gameVideo.videoId}">
			<input type="submit" value="Delete">
		</form>
	</c:if>
</body>
</html>
