<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<%@ taglib prefix="fmt" uri="jakarta.tags.fmt" %>
<jsp:include page="../common/header.jsp">
  <jsp:param name="title" value="${article.title}"/>
  <jsp:param name="menu" value="board"/>
  <jsp:param name="pageCss" value="board.css"/>
</jsp:include>

<div class="mb-4">
  <a href="${pageContext.request.contextPath}/free" class="btn btn-outline-secondary btn-sm">&larr; 목록으로</a>
</div>

<!-- 게시글 -->
<div class="card shadow-sm mb-4">
  <div class="card-header" style="background:var(--bg-card);border-bottom:1px solid var(--border-color)">
    <div class="d-flex justify-content-between align-items-center">
      <h5 class="mb-0">
        <c:choose>
          <c:when test="${article.cateName == '공지사항'}"><span class="badge badge-category-notice me-2">${article.cateName}</span></c:when>
          <c:when test="${article.cateName == '구장 리뷰'}"><span class="badge badge-category-review me-2">${article.cateName}</span></c:when>
          <c:when test="${article.cateName == '경기 소감'}"><span class="badge badge-category-impression me-2">${article.cateName}</span></c:when>
          <c:when test="${article.cateName == '팀원 모집'}"><span class="badge badge-category-recruit me-2">${article.cateName}</span></c:when>
          <c:when test="${article.cateName == '중고 거래'}"><span class="badge badge-category-trade me-2">${article.cateName}</span></c:when>
          <c:otherwise><span class="badge bg-secondary me-2">${article.cateName}</span></c:otherwise>
        </c:choose>
        ${article.title}
      </h5>
    </div>
  </div>
  <div class="card-body">
    <div class="article-meta">
      <div>
        <span class="me-3">작성자: <strong>${article.authorNickname}</strong></span>
        <span>작성일: <fmt:formatDate value="${article.createdAtAsDate}" pattern="yyyy-MM-dd HH:mm"/></span>
      </div>
      <div>조회수: ${article.views}</div>
    </div>
    <div class="article-content">${article.content}</div>
  </div>
  <div class="card-footer d-flex justify-content-end gap-2" style="background:var(--bg-card);border-top:1px solid var(--border-color)">
    <c:if test="${sessionScope.loginUser.userId == article.authorId}">
      <a href="${pageContext.request.contextPath}/free/edit/${article.articleId}" class="btn btn-warning btn-sm">수정</a>
      <form action="${pageContext.request.contextPath}/free/delete/${article.articleId}" method="post" class="d-inline" onsubmit="return confirm('정말 삭제하시겠습니까?');">
        <button type="submit" class="btn btn-danger btn-sm">삭제</button>
      </form>
    </c:if>
  </div>
</div>

<!-- 댓글 섹션 -->
<div class="comment-section">
  <div class="comment-section-header">
    댓글 <span style="color:var(--accent)">${comments.size()}</span>
  </div>

  <c:forEach var="comment" items="${comments}">
    <c:choose>
      <c:when test="${comment.parentId != null}">
        <div class="reply-item">
          <c:choose>
            <c:when test="${comment.deleted}">
              <div class="text-muted fst-italic small">삭제된 댓글입니다.</div>
            </c:when>
            <c:otherwise>
              <div class="comment-author-row">
                <span class="comment-author">↳ ${comment.nickname}</span>
                <span class="comment-date"><fmt:formatDate value="${comment.createdAtAsDate}" pattern="yyyy-MM-dd HH:mm"/></span>
                <c:if test="${sessionScope.loginUser.userId == comment.authorId}">
                  <form action="${pageContext.request.contextPath}/free/comment/delete" method="post" class="d-inline ms-auto" onsubmit="return confirm('댓글을 삭제하시겠습니까?');">
                    <input type="hidden" name="commentId" value="${comment.commentId}">
                    <input type="hidden" name="articleId" value="${article.articleId}">
                    <button type="submit" class="btn btn-outline-danger btn-sm" style="padding:2px 8px;font-size:0.75rem">삭제</button>
                  </form>
                </c:if>
              </div>
              <div class="comment-body">${comment.content}</div>
            </c:otherwise>
          </c:choose>
        </div>
      </c:when>
      <c:otherwise>
        <div class="comment-item">
          <c:choose>
            <c:when test="${comment.deleted}">
              <div class="text-muted fst-italic small">삭제된 댓글입니다.</div>
            </c:when>
            <c:otherwise>
              <div class="comment-author-row">
                <span class="comment-author">${comment.nickname}</span>
                <span class="comment-date"><fmt:formatDate value="${comment.createdAtAsDate}" pattern="yyyy-MM-dd HH:mm"/></span>
                <c:if test="${sessionScope.loginUser.userId == comment.authorId}">
                  <form action="${pageContext.request.contextPath}/free/comment/delete" method="post" class="d-inline ms-auto" onsubmit="return confirm('댓글을 삭제하시겠습니까?');">
                    <input type="hidden" name="commentId" value="${comment.commentId}">
                    <input type="hidden" name="articleId" value="${article.articleId}">
                    <button type="submit" class="btn btn-outline-danger btn-sm" style="padding:2px 8px;font-size:0.75rem">삭제</button>
                  </form>
                </c:if>
              </div>
              <div class="comment-body">${comment.content}</div>
              <c:if test="${sessionScope.loginUser.userId != null}">
                <button type="button" class="btn btn-outline-primary btn-sm mt-2" style="font-size:0.75rem;padding:3px 10px" onclick="toggleReplyForm(${comment.commentId})">답글</button>
                <div id="reply-form-${comment.commentId}" class="mt-2" style="display:none;">
                  <form action="${pageContext.request.contextPath}/free/comment/write" method="post">
                    <input type="hidden" name="articleId" value="${article.articleId}">
                    <input type="hidden" name="parentId" value="${comment.commentId}">
                    <textarea name="content" class="form-control mb-2" rows="2" placeholder="답글을 입력하세요" required></textarea>
                    <button type="submit" class="btn btn-primary btn-sm">답글 작성</button>
                  </form>
                </div>
              </c:if>
            </c:otherwise>
          </c:choose>
        </div>
      </c:otherwise>
    </c:choose>
  </c:forEach>

  <c:if test="${empty comments}">
    <div class="text-center text-muted py-4">첫 댓글을 남겨보세요!</div>
  </c:if>

  <!-- 댓글 작성 폼 -->
  <c:if test="${sessionScope.loginUser.userId != null}">
    <div class="comment-write-area">
      <div class="mb-2 fw-bold small" style="color:var(--accent)">댓글 작성</div>
      <form action="${pageContext.request.contextPath}/free/comment/write" method="post">
        <input type="hidden" name="articleId" value="${article.articleId}">
        <textarea name="content" class="form-control mb-2" rows="3" placeholder="댓글을 입력하세요" required></textarea>
        <div class="text-end">
          <button type="submit" class="btn btn-primary">댓글 작성</button>
        </div>
      </form>
    </div>
  </c:if>
  <c:if test="${sessionScope.loginUser.userId == null}">
    <div class="text-center text-muted py-3">
      댓글을 작성하려면 <a href="${pageContext.request.contextPath}/user/login" style="color:var(--accent)">로그인</a>이 필요합니다.
    </div>
  </c:if>
</div>

<script>
function toggleReplyForm(commentId) {
  const form = document.getElementById('reply-form-' + commentId);
  form.style.display = form.style.display === 'none' ? 'block' : 'none';
}
</script>

<jsp:include page="../common/footer.jsp"/>
