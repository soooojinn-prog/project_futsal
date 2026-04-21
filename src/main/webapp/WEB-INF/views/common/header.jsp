<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${param.title} - 렛츠풋살</title>
  <script>const contextPath = '${pageContext.request.contextPath}';</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,600;0,700;0,800;1,700&family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/bootstrap/bootstrap.min.css"/>
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/common/theme.css"/>
  <c:if test="${not empty param.pageCss}">
    <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/pages/${param.pageCss}"/>
  </c:if>
</head>
<body>
  <div class="header-accent-line"></div>
  <header>
    <div class="container py-2">
      <div class="d-flex align-items-center justify-content-between">
        <a href="${pageContext.request.contextPath}/" class="d-inline-flex align-items-center text-decoration-none">
          <img src="${pageContext.request.contextPath}/resources/image/logo/logo.png" height="42" alt="렛츠풋살 로고">
        </a>
        <div class="text-end">
          <c:choose>
            <%--@elvariable id="loginUser" type="io.github.wizwix.letsfutsal.dto.UserDTO"--%>
            <c:when test="${not empty loginUser}">
              <span class="small">${loginUser.nickname}님 환영합니다</span>
              <span class="mx-2" style="color:var(--border)">|</span>
              <a href="${pageContext.request.contextPath}/user/logout" class="small">로그아웃</a>
              <span class="mx-2" style="color:var(--border)">|</span>
              <a href="${pageContext.request.contextPath}/user/mypage" class="small">마이페이지</a>
            </c:when>
            <c:otherwise>
              <a href="${pageContext.request.contextPath}/user/login" class="small">로그인</a>
              <span class="mx-2" style="color:var(--border)">|</span>
              <a href="${pageContext.request.contextPath}/user/register" class="small">회원가입</a>
            </c:otherwise>
          </c:choose>
        </div>
      </div>
    </div>
  </header>
  <nav>
    <div class="container">
      <ul class="nav justify-content-center py-2">
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'match'   ? 'active' : ''}" href="${pageContext.request.contextPath}/match">매치</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'team'    ? 'active' : ''}" href="${pageContext.request.contextPath}/team">팀</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'stadium' ? 'active' : ''}" href="${pageContext.request.contextPath}/stadium">구장</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'rank'    ? 'active' : ''}" href="${pageContext.request.contextPath}/rank">랭킹</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'board'   ? 'active' : ''}" href="${pageContext.request.contextPath}/free">게시판</a>
        </li>
      </ul>
    </div>
  </nav>
  <main class="container py-4">
