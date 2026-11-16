<%@ taglib uri="http://java.sun.com/jsp/jstl/functions" prefix="fn" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/fmt" prefix="fmt" %>

<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<title>Delete Genre</title>
</head>
<body>
	<h1>Delete Genre</h1>
	<p><a href="genres">Back to Genres</a></p>
	<p><span style="color:green"><b>${messages.success}</b></span></p>
	<p><span style="color:red"><b>${messages.error}</b></span></p>

	<form action="genredelete" method="get">
		<label for="genreId">genreId</label>
		<input id="genreId" name="genreId" value="${fn:escapeXml(param.genreId)}">
		<input type="submit" value="Load">
	</form>
	<br/>

	<c:if test="${not empty genre}">
		<p>Are you sure you want to delete genre_id=${genre.genreId}, name=<c:out value="${genre.name}"/>?</p>
		<form action="genredelete" method="post">
			<input type="hidden" name="genreId" value="${genre.genreId}">
			<input type="submit" value="Delete">
		</form>
	</c:if>
</body>
</html>
