<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="구장"/>
  <jsp:param name="menu" value="stadium"/>
  <jsp:param name="pageCss" value="team-stadium.css"/>
</jsp:include>
<div class="ts-main-hero">
  <h2 class="ts-main-hero-title">구장 관리</h2>
  <p class="ts-main-hero-sub">풋살을 즐길 수 있는 구장을 찾아보세요</p>
  <div class="d-flex justify-content-center gap-3 mt-4">
    <a href="${pageContext.request.contextPath}/stadium/list" class="btn btn-primary btn-lg">모든 구장 보기</a>
  </div>
</div>
<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
