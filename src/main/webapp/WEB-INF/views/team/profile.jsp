<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="${team.teamName}"/>
  <jsp:param name="menu" value="team"/>
  <jsp:param name="pageCss" value="team-stadium.css"/>
</jsp:include>
<script>
  const isLogin = ${loginUser != null};
  function joinTeam() {
    if (!isLogin) {
      alert("로그인 후 가입 가능합니다.");
      return;
    }
    const isConfirmed = confirm("닉네임 : ${loginUser.nickname}\n팀 이름 : ${team.teamName}\n\n해당 팀에 가입하시겠습니까?");
    if (isConfirmed) {
      alert("가입이 완료되었습니다!");
      location.href = "${pageContext.request.contextPath}/team/list";
    }
  }
</script>

<div class="row g-4">
  <div class="col-lg-8">
    <div class="ts-profile-card">
      <div class="ts-profile-hero">
        <div class="ts-profile-name">${team.teamName}</div>
        <div class="ts-profile-sub">${team.region}</div>
      </div>
      <div class="ts-profile-body">
        <div class="ts-info-row">
          <span class="ts-info-label">성별</span>
          <span class="ts-info-value">
            <c:choose>
              <c:when test="${team.gender == 'BOTH'}">혼성</c:when>
              <c:when test="${team.gender == 'MALE'}">남성</c:when>
              <c:when test="${team.gender == 'FEMALE'}">여성</c:when>
              <c:otherwise>-</c:otherwise>
            </c:choose>
          </span>
        </div>
        <div class="ts-info-row">
          <span class="ts-info-label">등급</span>
          <span class="ts-info-value">
            <c:choose><c:when test="${team.minGrade==0}">입문</c:when><c:when test="${team.minGrade==1}">초보</c:when><c:when test="${team.minGrade==2}">중수</c:when><c:otherwise>고수</c:otherwise></c:choose>
            ~
            <c:choose><c:when test="${team.maxGrade==0}">입문</c:when><c:when test="${team.maxGrade==1}">초보</c:when><c:when test="${team.maxGrade==2}">중수</c:when><c:otherwise>고수</c:otherwise></c:choose>
          </span>
        </div>
        <div class="ts-info-row">
          <span class="ts-info-label">지역</span>
          <span class="ts-info-value">${team.region}</span>
        </div>
        <div class="ts-info-row">
          <span class="ts-info-label">팀 주장</span>
          <span class="ts-info-value" style="color:var(--accent);font-weight:600">${team.leaderNickname}</span>
        </div>
        <c:if test="${not empty team.introduction}">
          <div class="ts-info-row" style="flex-direction:column;align-items:flex-start;gap:8px">
            <span class="ts-info-label">팀 소개</span>
            <span class="ts-info-value" style="color:var(--text-2);line-height:1.7">${team.introduction}</span>
          </div>
        </c:if>
      </div>
      <div class="ts-profile-footer">
        <button type="button" class="btn btn-primary" onclick="joinTeam()">팀 가입하기</button>
        <a href="${pageContext.request.contextPath}/team/list" class="btn btn-outline-secondary">팀 목록으로</a>
      </div>
    </div>
  </div>
</div>
<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
