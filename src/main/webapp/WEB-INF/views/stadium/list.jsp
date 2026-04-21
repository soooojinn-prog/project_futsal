<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="jakarta.tags.core"%>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="구장 목록"/>
  <jsp:param name="menu" value="stadium"/>
  <jsp:param name="pageCss" value="team-stadium.css"/>
</jsp:include>

<div class="page-hero">
  <h2>구장 목록</h2>
  <div class="page-hero-bar"></div>
</div>

<c:choose>
  <c:when test="${empty stadiums}">
    <div class="alert alert-info text-center py-5">등록된 구장이 없습니다.</div>
  </c:when>
  <c:otherwise>
    <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
      <c:forEach var="stadium" items="${stadiums}" varStatus="vs">
        <div class="col">
          <div class="ts-card delay-${vs.index < 6 ? vs.index : 5}">
            <div class="ts-card-accent-bar"></div>
            <div class="ts-card-body">
              <div class="ts-card-name">${stadium.name}</div>
              <div class="ts-card-info">
                <span class="ts-card-tag">${stadium.region}</span>
                <span class="ts-card-tag">${stadium.startHour} ~ ${stadium.endHour}</span>
              </div>
              <div class="ts-card-sub">${stadium.location}</div>
            </div>
            <div class="ts-card-footer">
              <a href="${pageContext.request.contextPath}/stadium/profile/${stadium.stadiumId}" class="btn btn-sm btn-primary w-100">상세보기</a>
            </div>
          </div>
        </div>
      </c:forEach>
    </div>
  </c:otherwise>
</c:choose>

<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
