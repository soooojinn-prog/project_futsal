<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="팀 목록"/>
  <jsp:param name="menu" value="team"/>
  <jsp:param name="pageCss" value="team-stadium.css"/>
</jsp:include>

<div class="d-flex justify-content-between align-items-center mb-4">
  <div class="page-hero mb-0">
    <h2>팀 목록</h2>
    <div class="page-hero-bar"></div>
  </div>
  <a href="${pageContext.request.contextPath}/team/create" class="btn btn-primary">팀 생성하기</a>
</div>

<c:choose>
  <c:when test="${empty teams}">
    <div class="alert alert-info text-center py-5">등록된 팀이 없습니다.</div>
  </c:when>
  <c:otherwise>
    <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
      <c:forEach var="team" items="${teams}" varStatus="vs">
        <div class="col">
          <div class="ts-card delay-${vs.index < 6 ? vs.index : 5}">
            <div class="ts-card-accent-bar"></div>
            <div class="ts-card-body">
              <div class="ts-card-name">${team.teamName}</div>
              <div class="ts-card-info">
                <span class="ts-card-tag">${team.region}</span>
                <span class="ts-card-tag">
                  <c:choose>
                    <c:when test="${team.gender=='BOTH'}">혼성</c:when>
                    <c:when test="${team.gender=='MALE'}">남성</c:when>
                    <c:when test="${team.gender=='FEMALE'}">여성</c:when>
                    <c:otherwise>-</c:otherwise>
                  </c:choose>
                </span>
                <span class="ts-card-tag">
                  <c:choose><c:when test="${team.minGrade==0}">입문</c:when><c:when test="${team.minGrade==1}">초보</c:when><c:when test="${team.minGrade==2}">중수</c:when><c:otherwise>고수</c:otherwise></c:choose>~<c:choose><c:when test="${team.maxGrade==0}">입문</c:when><c:when test="${team.maxGrade==1}">초보</c:when><c:when test="${team.maxGrade==2}">중수</c:when><c:otherwise>고수</c:otherwise></c:choose>
                </span>
              </div>
            </div>
            <div class="ts-card-footer">
              <a href="${pageContext.request.contextPath}/team/profile/${team.teamId}" class="btn btn-sm btn-primary w-100">상세보기</a>
            </div>
          </div>
        </div>
      </c:forEach>
    </div>
  </c:otherwise>
</c:choose>

<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
