<%@ taglib uri="http://java.sun.com/jsp/jstl/functions" prefix="fn" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/core" prefix="c" %>
<%@ taglib uri="http://java.sun.com/jsp/jstl/fmt" prefix="fmt" %>

<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<title>Create GameVideo</title>
</head>
<body>
	<h1>Create GameVideo</h1>
	<p><a href="gamedetail">Back to Game Detail</a></p>
	<p><span style="color:green"><b>${messages.success}</b></span></p>
	<p><span style="color:red"><b>${messages.error}</b></span></p>

	<form action="videocreate" method="post">
		<p>
			<label for="appId">appId</label>
			<input id="appId" name="appId" value="">
		</p>
		<p>
			<label for="name">Name</label>
			<input id="name" name="name" value="">
		</p>
		<p>
			<label for="url">url</label>
			<input id="url" name="url" value="">
		</p>
		<p>
			<label for="videoUrl">video_url</label>
			<input id="videoUrl" name="videoUrl" value="">
		</p>
		<p>
			<label for="videoType">video_type</label>
			<select id="videoType" name="videoType">
				<option value="trailer">trailer</option>
				<option value="gameplay">gameplay</option>
				<option value="screenshot">screenshot</option>
			</select>
		</p>
		<p><input type="submit" value="Create"></p>
	</form>
</body>
</html>
