<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<%@ taglib prefix="fmt" uri="jakarta.tags.fmt" %>
<jsp:include page="../common/header.jsp">
  <jsp:param name="title" value="자유게시판"/>
  <jsp:param name="menu" value="board"/>
  <jsp:param name="pageCss" value="board.css"/>
</jsp:include>

<div class="d-flex justify-content-between align-items-center mb-4">
  <div class="page-hero mb-0">
    <h2>자유게시판</h2>
    <div class="page-hero-bar"></div>
  </div>
  <a href="${pageContext.request.contextPath}/free/write" class="btn btn-primary">글쓰기</a>
</div>

<!-- 게시글 목록 -->
<div class="card shadow-sm">
  <div class="table-responsive">
    <table class="table table-hover board-table mb-0">
      <thead class="table-dark">
        <tr>
          <th width="8%">번호</th>
          <th width="12%">카테고리</th>
          <th width="40%">제목</th>
          <th width="12%">작성자</th>
          <th width="15%">작성일</th>
          <th width="8%">조회수</th>
        </tr>
      </thead>
      <tbody>
        <c:forEach var="article" items="${articles}">
          <tr>
            <td>${article.articleId}</td>
            <td>
              <c:choose>
                <c:when test="${article.cateName == '공지사항'}"><span class="badge badge-category-notice">${article.cateName}</span></c:when>
                <c:when test="${article.cateName == '구장 리뷰'}"><span class="badge badge-category-review">${article.cateName}</span></c:when>
                <c:when test="${article.cateName == '경기 소감'}"><span class="badge badge-category-impression">${article.cateName}</span></c:when>
                <c:when test="${article.cateName == '팀원 모집'}"><span class="badge badge-category-recruit">${article.cateName}</span></c:when>
                <c:when test="${article.cateName == '중고 거래'}"><span class="badge badge-category-trade">${article.cateName}</span></c:when>
                <c:otherwise><span class="badge bg-secondary">${article.cateName}</span></c:otherwise>
              </c:choose>
            </td>
            <td>
              <a href="${pageContext.request.contextPath}/free/view/${article.articleId}" class="text-decoration-none text-dark">
                ${article.title}
              </a>
            </td>
            <td>${article.authorNickname}</td>
            <td><fmt:formatDate value="${article.createdAtAsDate}" pattern="yyyy-MM-dd HH:mm"/></td>
            <td>${article.views}</td>
          </tr>
        </c:forEach>
        <c:if test="${empty articles}">
          <tr>
            <td colspan="6" class="text-center py-4 text-muted">게시글이 없습니다.</td>
          </tr>
        </c:if>
      </tbody>
    </table>
  </div>
</div>

<!-- 페이지네이션 -->
<nav class="mt-4">
  <ul class="pagination justify-content-center">
    <c:if test="${currentPage > 1}">
      <li class="page-item">
        <c:choose>
          <c:when test="${currentPage == 2}">
            <a class="page-link" href="${pageContext.request.contextPath}/free">&laquo; 이전</a>
          </c:when>
          <c:otherwise>
            <a class="page-link" href="${pageContext.request.contextPath}/free/page/${currentPage - 1}">&laquo; 이전</a>
          </c:otherwise>
        </c:choose>
      </li>
    </c:if>

    <c:forEach begin="1" end="${totalPages}" var="i">
      <li class="page-item ${currentPage == i ? 'active' : ''}">
        <c:choose>
          <c:when test="${i == 1}">
            <a class="page-link" href="${pageContext.request.contextPath}/free">${i}</a>
          </c:when>
          <c:otherwise>
            <a class="page-link" href="${pageContext.request.contextPath}/free/page/${i}">${i}</a>
          </c:otherwise>
        </c:choose>
      </li>
    </c:forEach>

    <c:if test="${currentPage < totalPages}">
      <li class="page-item">
        <a class="page-link" href="${pageContext.request.contextPath}/free/page/${currentPage + 1}">다음 &raquo;</a>
      </li>
    </c:if>
  </ul>
</nav>

<!-- 검색 -->
<div class="card search-card mt-4">
  <div class="card-body">
    <form action="${pageContext.request.contextPath}/free/search" method="get" class="row g-2 justify-content-center">
      <div class="col-auto">
        <select name="searchType" class="form-select">
          <option value="title">제목</option>
          <option value="content">내용</option>
          <option value="nickname">닉네임</option>
          <option value="comment">댓글 내용</option>
        </select>
      </div>
      <div class="col-auto">
        <input type="text" name="query" class="form-control" placeholder="검색어 입력" required>
      </div>
      <div class="col-auto">
        <button type="submit" class="btn btn-primary">검색</button>
      </div>
    </form>
  </div>
</div>

<jsp:include page="../common/footer.jsp"/>
