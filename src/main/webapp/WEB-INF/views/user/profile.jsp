<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="${user.nickname}님의 프로필"/>
  <jsp:param name="menu" value="user"/>
  <jsp:param name="pageCss" value="user.css"/>
</jsp:include>
<div class="row justify-content-center">
  <div class="col-lg-6">
    <div class="profile-card">
      <div class="profile-avatar">${user.nickname.charAt(0)}</div>
      <div class="profile-nickname">${user.nickname}</div>
      <div class="profile-badges">
        <span class="grade-badge">
          <c:choose>
            <c:when test="${user.grade==0}">입문</c:when>
            <c:when test="${user.grade==1}">초보</c:when>
            <c:when test="${user.grade==2}">중수</c:when>
            <c:otherwise>고수</c:otherwise>
          </c:choose>
        </span>
      </div>
      <div class="point-highlight">${user.point} <span>P</span></div>
      <table class="profile-table mt-3">
        <tr>
          <th>성별</th>
          <td>
            <c:choose>
              <c:when test="${user.gender=='MALE'}">남성</c:when>
              <c:when test="${user.gender=='FEMALE'}">여성</c:when>
              <c:otherwise>${user.gender}</c:otherwise>
            </c:choose>
          </td>
        </tr>
        <tr>
          <th>선호 포지션</th>
          <td>
            <c:choose>
              <c:when test="${empty user.preferredPosition}"><span class="text-muted">설정 안 함</span></c:when>
              <c:otherwise>${user.preferredPosition}</c:otherwise>
            </c:choose>
          </td>
        </tr>
        <tr>
          <th>가입일</th>
          <td>${user.createdAt}</td>
        </tr>
      </table>
      <c:if test="${not empty user.introduction}">
        <div class="mt-4 text-start w-100">
          <div class="text-muted small mb-1" style="color:var(--accent)!important;font-weight:600">자기소개</div>
          <p class="text-muted mb-0" style="line-height:1.7">${user.introduction}</p>
        </div>
      </c:if>
      <div class="mt-4 d-flex gap-2">
        <a href="${pageContext.request.contextPath}/user/list" class="btn btn-outline-primary">회원 목록</a>
        <a href="${pageContext.request.contextPath}/" class="btn btn-outline-secondary">홈으로</a>
      </div>
    </div>
  </div>
</div>
<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
