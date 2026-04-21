<%@ page contentType="text/html;charset=UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="${stadium.name}"/>
  <jsp:param name="menu" value="stadium"/>
  <jsp:param name="pageCss" value="team-stadium.css"/>
</jsp:include>
<div class="row g-4">
  <div class="col-lg-8">
    <div class="ts-profile-card">
      <div class="ts-profile-hero">
        <div class="ts-profile-name">${stadium.name}</div>
        <div class="ts-profile-sub">${stadium.region}</div>
      </div>
      <div class="ts-profile-body">
        <div class="ts-info-row">
          <span class="ts-info-label">지역</span>
          <span class="ts-info-value">${stadium.region}</span>
        </div>
        <div class="ts-info-row">
          <span class="ts-info-label">주소</span>
          <span class="ts-info-value">${stadium.location}</span>
        </div>
        <div class="ts-info-row">
          <span class="ts-info-label">운영시간</span>
          <span class="ts-info-value" style="color:var(--accent);font-weight:600">${stadium.startHour} ~ ${stadium.endHour}</span>
        </div>
        <c:if test="${not empty stadium.introduction}">
          <div class="ts-info-row" style="flex-direction:column;align-items:flex-start;gap:8px">
            <span class="ts-info-label">구장 소개</span>
            <span class="ts-info-value" style="color:var(--text-2);line-height:1.7">${stadium.introduction}</span>
          </div>
        </c:if>
      </div>
      <div class="ts-profile-footer">
        <c:choose>
          <c:when test="${empty loginUser}">
            <button class="btn btn-secondary" disabled>로그인 후 예약 가능</button>
          </c:when>
          <c:otherwise>
            <a href="${pageContext.request.contextPath}/stadium/rent/${stadium.stadiumId}" class="btn btn-primary">대여 예약하기</a>
          </c:otherwise>
        </c:choose>
        <a href="${pageContext.request.contextPath}/stadium/list" class="btn btn-outline-secondary">구장 목록으로</a>
      </div>
    </div>
  </div>
</div>
<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
