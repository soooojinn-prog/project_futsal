<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<jsp:include page="../common/header.jsp">
  <jsp:param name="title" value="매치 상세"/>
  <jsp:param name="menu" value="match"/>
  <jsp:param name="pageCss" value="match.css"/>
</jsp:include>

<div class="mb-4">
  <a href="${pageContext.request.contextPath}/match" class="btn btn-outline-secondary btn-sm">&larr; 목록으로</a>
</div>

<div class="row g-4">
  <div class="col-lg-8">
    <div class="match-detail-card">
      <div class="match-detail-header">
        <c:choose>
          <c:when test="${match.matchType == 'INDIVIDUAL'}"><span class="badge badge-individual">개인 경기</span></c:when>
          <c:when test="${match.matchType == 'TEAM'}"><span class="badge badge-team">팀 경기</span></c:when>
          <c:otherwise><span class="badge badge-rent">대여</span></c:otherwise>
        </c:choose>
        <h4 class="match-detail-title">${match.stadiumName}</h4>
      </div>
      <div class="match-detail-body">
        <div class="match-info-row">
          <span class="match-info-label">경기 ID</span>
          <span class="match-info-value">${match.matchId}</span>
        </div>
        <div class="match-info-row">
          <span class="match-info-label">구장</span>
          <span class="match-info-value fw-bold">${match.stadiumName}</span>
        </div>
        <div class="match-info-row">
          <span class="match-info-label">경기 날짜</span>
          <span class="match-info-value">${match.matchDate}</span>
        </div>
        <div class="match-info-row">
          <span class="match-info-label">경기 시간</span>
          <span class="match-info-value">${match.startHour} ~ ${match.endHour}</span>
        </div>
        <div class="match-info-row">
          <span class="match-info-label">성별</span>
          <span class="match-info-value">
            <c:choose>
              <c:when test="${match.gender == 'MALE'}"><span class="badge bg-primary">남성</span></c:when>
              <c:when test="${match.gender == 'FEMALE'}"><span class="badge bg-danger">여성</span></c:when>
              <c:otherwise><span class="badge bg-success">혼성</span></c:otherwise>
            </c:choose>
          </span>
        </div>
        <div class="match-info-row">
          <span class="match-info-label">등급 범위</span>
          <span class="match-info-value">
            <c:choose><c:when test="${match.minGrade==0}">입문</c:when><c:when test="${match.minGrade==1}">초보</c:when><c:when test="${match.minGrade==2}">중수</c:when><c:otherwise>고수</c:otherwise></c:choose>
            ~
            <c:choose><c:when test="${match.maxGrade==0}">입문</c:when><c:when test="${match.maxGrade==1}">초보</c:when><c:when test="${match.maxGrade==2}">중수</c:when><c:otherwise>고수</c:otherwise></c:choose>
          </span>
        </div>
        <div class="match-info-row">
          <span class="match-info-label">참여 현황</span>
          <span class="match-info-value">
            <span class="fs-5 fw-bold" style="color:var(--accent)">${match.status}</span>
            <span class="text-muted">/ 10명</span>
            <c:if test="${match.status < 10}"><span class="badge bg-success ms-2">참여 가능</span></c:if>
            <c:if test="${match.status >= 10}"><span class="badge bg-danger ms-2">마감</span></c:if>
          </span>
        </div>
      </div>
      <div class="match-detail-footer">
        <c:if test="${match.status < 10}">
          <button class="btn btn-primary">참여 신청</button>
        </c:if>
        <c:if test="${match.status >= 10}">
          <button class="btn btn-secondary" disabled>마감되었습니다</button>
        </c:if>
      </div>
    </div>
  </div>

  <div class="col-lg-4">
    <div class="match-join-card">
      <div class="match-join-title">참여 현황</div>
      <div class="match-capacity-bar">
        <div class="match-capacity-fill" style="width: ${match.status * 10}%"></div>
      </div>
      <div class="match-capacity-text">
        <span>${match.status}명 참여 중</span>
        <span>최대 10명</span>
      </div>
      <p class="text-muted small mt-3 mb-0">
        <c:choose>
          <c:when test="${match.status == 0}">아직 참여자가 없습니다.</c:when>
          <c:when test="${match.status < 5}">참여자를 모집 중입니다.</c:when>
          <c:when test="${match.status < 10}">곧 마감됩니다!</c:when>
          <c:otherwise>모집이 완료되었습니다.</c:otherwise>
        </c:choose>
      </p>
    </div>
  </div>
</div>

<jsp:include page="../common/footer.jsp"/>
