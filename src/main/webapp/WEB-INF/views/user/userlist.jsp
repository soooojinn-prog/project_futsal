<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="회원 목록"/>
  <jsp:param name="menu" value="user"/>
  <jsp:param name="pageCss" value="user.css"/>
</jsp:include>
<div class="d-flex justify-content-between align-items-center mb-4">
  <div class="page-hero mb-0">
    <h2>회원 목록</h2>
    <div class="page-hero-bar"></div>
  </div>
  <div class="d-flex align-items-center gap-2">
    <label for="sortBy" class="form-label mb-0 text-muted small">정렬:</label>
    <select class="form-select form-select-sm" id="sortBy" style="width: auto;" onchange="location.href='${pageContext.request.contextPath}/user/list?sortBy=' + this.value;">
      <option value="point" ${currentSort == 'point' ? 'selected' : ''}>포인트 높은 순</option>
      <option value="grade" ${currentSort == 'grade' ? 'selected' : ''}>등급 높은 순</option>
      <option value="nickname" ${currentSort == 'nickname' ? 'selected' : ''}>닉네임 순</option>
    </select>
  </div>
</div>
<c:choose>
  <c:when test="${empty users}">
    <div class="alert alert-info text-center py-5">등록된 회원이 없습니다.</div>
  </c:when>
  <c:otherwise>
    <div class="card shadow-sm">
      <div class="table-responsive">
        <table class="table table-hover board-table mb-0">
          <thead class="table-dark">
            <tr>
              <th style="width: 60px;">순위</th>
              <th>닉네임</th>
              <th>성별</th>
              <th>포지션</th>
              <th>포인트</th>
              <th>등급</th>
            </tr>
          </thead>
          <tbody>
            <c:forEach var="user" items="${users}" varStatus="status">
              <tr>
                <td class="text-center rank-number">${status.index + 1}</td>
                <td>
                  <a href="${pageContext.request.contextPath}/user/profile/${user.userId}" class="text-decoration-none">${user.nickname}</a>
                </td>
                <td>
                  <c:choose>
                    <c:when test="${user.gender=='MALE'}">남성</c:when>
                    <c:when test="${user.gender=='FEMALE'}">여성</c:when>
                    <c:otherwise>${user.gender}</c:otherwise>
                  </c:choose>
                </td>
                <td>
                  <c:choose>
                    <c:when test="${empty user.preferredPosition}"><span class="text-muted">-</span></c:when>
                    <c:otherwise>${user.preferredPosition}</c:otherwise>
                  </c:choose>
                </td>
                <td><span class="badge" style="background:rgba(0,200,120,0.15);color:var(--accent);border:1px solid rgba(0,200,120,0.3)">${user.point} P</span></td>
                <td>
                  <span class="grade-badge">
                    <c:choose>
                      <c:when test="${user.grade==0}">입문</c:when>
                      <c:when test="${user.grade==1}">초보</c:when>
                      <c:when test="${user.grade==2}">중수</c:when>
                      <c:otherwise>고수</c:otherwise>
                    </c:choose>
                  </span>
                </td>
              </tr>
            </c:forEach>
          </tbody>
        </table>
      </div>
    </div>
  </c:otherwise>
</c:choose>
<div class="mt-4">
  <a href="${pageContext.request.contextPath}/" class="btn btn-secondary">홈으로</a>
</div>
<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
