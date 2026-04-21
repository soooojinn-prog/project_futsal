<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<jsp:include page="../common/header.jsp">
  <jsp:param name="title" value="매치 목록"/>
  <jsp:param name="menu" value="match"/>
  <jsp:param name="pageCss" value="match.css"/>
</jsp:include>
<%
  var tab = request.getParameter("tab");
  if (tab == null) tab = "all";
  pageContext.setAttribute("currentTab", tab);
  String matchType = null;
  if ("individual".equals(tab)) matchType = "INDIVIDUAL";
  else if ("team".equals(tab))  matchType = "TEAM";
  else if ("rent".equals(tab))  matchType = "RENT";
  pageContext.setAttribute("matchType", matchType);
%>

<div class="page-hero">
  <h2>매치 목록</h2>
  <div class="page-hero-bar"></div>
</div>

<ul class="nav nav-tabs mb-4">
  <li class="nav-item">
    <a class="nav-link ${currentTab == 'all'        ? 'active' : ''}" href="${pageContext.request.contextPath}/match?tab=all">전체</a>
  </li>
  <li class="nav-item">
    <a class="nav-link ${currentTab == 'individual' ? 'active' : ''}" href="${pageContext.request.contextPath}/match?tab=individual&type=INDIVIDUAL">개인 경기</a>
  </li>
  <li class="nav-item">
    <a class="nav-link ${currentTab == 'team'       ? 'active' : ''}" href="${pageContext.request.contextPath}/match?tab=team&type=TEAM">팀 경기</a>
  </li>
  <li class="nav-item">
    <a class="nav-link ${currentTab == 'rent'       ? 'active' : ''}" href="${pageContext.request.contextPath}/match?tab=rent&type=RENT">대여</a>
  </li>
</ul>

<div class="card filter-card mb-4">
  <div class="card-body">
    <form method="get" class="row g-3">
      <input type="hidden" name="tab" value="${currentTab}">
      <input type="hidden" name="type" value="${matchType}">
      <div class="col-md-4">
        <label class="form-label">지역</label>
        <select name="region" class="form-select">
          <option value="">전체</option>
          <option value="서울" ${region=='서울'?'selected':''}>서울</option>
          <option value="경기" ${region=='경기'?'selected':''}>경기</option>
          <option value="강원" ${region=='강원'?'selected':''}>강원</option>
          <option value="충북" ${region=='충북'?'selected':''}>충북</option>
          <option value="충남" ${region=='충남'?'selected':''}>충남</option>
          <option value="전북" ${region=='전북'?'selected':''}>전북</option>
          <option value="전남" ${region=='전남'?'selected':''}>전남</option>
          <option value="경북" ${region=='경북'?'selected':''}>경북</option>
          <option value="경남" ${region=='경남'?'selected':''}>경남</option>
          <option value="제주" ${region=='제주'?'selected':''}>제주</option>
        </select>
      </div>
      <div class="col-md-4">
        <label class="form-label">성별</label>
        <select name="gender" class="form-select">
          <option value="">전체</option>
          <option value="BOTH"   ${gender=='BOTH'  ?'selected':''}>혼성</option>
          <option value="MALE"   ${gender=='MALE'  ?'selected':''}>남성</option>
          <option value="FEMALE" ${gender=='FEMALE'?'selected':''}>여성</option>
        </select>
      </div>
      <div class="col-md-4">
        <label class="form-label">등급</label>
        <div class="input-group">
          <select name="minGrade" class="form-select">
            <option value="">최소</option>
            <option value="0" ${minGrade==0?'selected':''}>입문</option>
            <option value="1" ${minGrade==1?'selected':''}>초보</option>
            <option value="2" ${minGrade==2?'selected':''}>중수</option>
            <option value="3" ${minGrade==3?'selected':''}>고수</option>
          </select>
          <span class="input-group-text">~</span>
          <select name="maxGrade" class="form-select">
            <option value="">최대</option>
            <option value="0" ${maxGrade==0?'selected':''}>입문</option>
            <option value="1" ${maxGrade==1?'selected':''}>초보</option>
            <option value="2" ${maxGrade==2?'selected':''}>중수</option>
            <option value="3" ${maxGrade==3?'selected':''}>고수</option>
          </select>
        </div>
      </div>
      <div class="col-12 d-flex gap-2">
        <button type="submit" class="btn btn-primary">검색</button>
        <a href="${pageContext.request.contextPath}/match?tab=${currentTab}<c:if test='${matchType != null}'>&type=${matchType}</c:if>" class="btn btn-secondary">초기화</a>
      </div>
    </form>
  </div>
</div>

<div class="row g-4">
  <c:forEach var="m" items="${matches}" varStatus="vs">
    <div class="col-12 col-md-6 col-lg-4">
      <div class="match-list-card
        <c:choose>
          <c:when test="${m.matchType == 'INDIVIDUAL'}">type-individual</c:when>
          <c:when test="${m.matchType == 'TEAM'}">type-team</c:when>
          <c:otherwise>type-rent</c:otherwise>
        </c:choose>
        delay-${vs.index < 6 ? vs.index : 5}">
        <div class="match-list-card-bar"></div>
        <div class="match-list-card-body">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <c:choose>
              <c:when test="${m.matchType == 'INDIVIDUAL'}"><span class="badge badge-individual">개인</span></c:when>
              <c:when test="${m.matchType == 'TEAM'}">      <span class="badge badge-team">팀</span></c:when>
              <c:otherwise>                                 <span class="badge badge-rent">대여</span></c:otherwise>
            </c:choose>
            <span class="match-list-time">${m.startHour} ~ ${m.endHour}</span>
          </div>
          <div class="match-list-stadium">${m.stadiumName}</div>
          <div class="match-list-info">
            ${m.region} &nbsp;·&nbsp;
            <c:choose>
              <c:when test="${m.gender=='MALE'}">남성</c:when>
              <c:when test="${m.gender=='FEMALE'}">여성</c:when>
              <c:otherwise>혼성</c:otherwise>
            </c:choose>
            &nbsp;·&nbsp;
            <c:choose><c:when test="${m.minGrade==0}">입문</c:when><c:when test="${m.minGrade==1}">초보</c:when><c:when test="${m.minGrade==2}">중수</c:when><c:otherwise>고수</c:otherwise></c:choose>~<c:choose><c:when test="${m.maxGrade==0}">입문</c:when><c:when test="${m.maxGrade==1}">초보</c:when><c:when test="${m.maxGrade==2}">중수</c:when><c:otherwise>고수</c:otherwise></c:choose>
          </div>
          <div class="d-flex justify-content-between align-items-center mt-auto">
            <span class="match-list-status"><span class="count">${m.status}</span>명 참여중</span>
            <a href="${pageContext.request.contextPath}/match/${m.matchId}" class="btn btn-sm btn-primary">상세보기</a>
          </div>
          <div class="mt-2" style="font-size:0.75rem;color:var(--text-3)">${m.matchDate}</div>
        </div>
      </div>
    </div>
  </c:forEach>
  <c:if test="${empty matches}">
    <div class="col-12">
      <div class="alert alert-secondary text-center py-5">검색 결과가 없습니다.</div>
    </div>
  </c:if>
</div>

<jsp:include page="../common/footer.jsp"/>
