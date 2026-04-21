<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="팀"/>
  <jsp:param name="menu" value="team"/>
  <jsp:param name="pageCss" value="team-stadium.css"/>
</jsp:include>
<div class="ts-main-hero">
  <h2 class="ts-main-hero-title">팀 관리</h2>
  <p class="ts-main-hero-sub">나만의 풋살 팀을 만들고 함께할 팀원을 찾아보세요</p>
  <div class="d-flex justify-content-center gap-3 mt-4">
    <a href="${pageContext.request.contextPath}/team/list" class="btn btn-primary btn-lg">모든 팀 보기</a>
    <a href="${pageContext.request.contextPath}/team/create" class="btn btn-outline-primary btn-lg">팀 생성하기</a>
  </div>
</div>
<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
