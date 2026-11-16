<%@ taglib uri="http://java.sun.com/jsp/jstl/functions" prefix="fn" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/fmt" prefix="fmt" %>

<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<title>Genres</title>
</head>
<body>
	<h1>Genres</h1>
	<p><a href="gamedetail">Back to Game Detail</a></p>
	<p><span style="color:green"><b>${messages.success}</b></span></p>
	<p><span style="color:red"><b>${messages.error}</b></span></p>

	<h2>Create Genre</h2>
	<form action="genres" method="post">
		<p>
			<label for="name">Name</label>
			<input id="name" name="name" value="">
		</p>
		<p><input type="submit" value="Create"></p>
	</form>

	<h2>All Genres</h2>
	<c:choose>
		<c:when test="${empty genres}">
			<p>No genres.</p>
		</c:when>
		<c:otherwise>
			<table border="1">
				<tr><th>genre_id</th><th>name</th><th></th><th></th></tr>
				<c:forEach var="g" items="${genres}">
					<tr>
						<td><c:out value="${g.genreId}"/></td>
						<td><c:out value="${g.name}"/></td>
						<td><a href="genreupdate?genreId=${g.genreId}">Update</a></td>
						<td><a href="genredelete?genreId=${g.genreId}">Delete</a></td>
					</tr>
				</c:forEach>
			</table>
		</c:otherwise>
	</c:choose>
</body>
</html>
