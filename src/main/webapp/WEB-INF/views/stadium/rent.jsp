<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="jakarta.tags.core"%>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="구장 대여"/>
  <jsp:param name="menu" value="stadium"/>
  <jsp:param name="pageCss" value="team-stadium.css"/>
</jsp:include>
<script>
  function confirmRent() {
    const time = document.querySelector('input[name="rentTime"]:checked');
    if (!time) {
      alert("대여 시간을 선택해주세요.");
      return false;
    }
    const isConfirmed = confirm(
        "닉네임 : ${loginUser.nickname}\n" +
        "구장 : ${stadium.name}\n" +
        "대여 시간 : " + time.value + "\n\n" +
        "대여하시겠습니까?"
    );
    if (isConfirmed) {
      alert("예약이 완료되었습니다!");
      return true;
    }
    return false;
  }
</script>
<div class="page-hero">
  <h2>구장 대여 예약</h2>
  <div class="page-hero-bar"></div>
</div>
<div class="row justify-content-center">
  <div class="col-lg-6">
    <div class="card shadow-sm">
      <div class="card-body p-4">
        <div class="mb-4 p-3 rounded" style="background:rgba(0,200,120,0.05);border:1px solid rgba(0,200,120,0.15)">
          <p class="mb-1"><strong style="color:var(--accent)">구장:</strong> ${stadium.name}</p>
          <p class="mb-0"><strong style="color:var(--accent)">운영시간:</strong> ${stadium.startHour} ~ ${stadium.endHour}</p>
        </div>
        <form action="${pageContext.request.contextPath}/stadium/rent/confirm" method="post" <c:if test="${not empty loginUser}">onsubmit="return confirmRent()"</c:if>>
          <input type="hidden" name="stadiumId" value="${stadium.stadiumId}">
          <h6 class="fw-bold mb-3">대여 시간 선택</h6>
          <c:set var="hour" value="${stadium.startHour.hour}" />
          <c:set var="end" value="${stadium.endHour.hour}" />
          <div class="d-flex flex-wrap gap-2 mb-4">
            <c:forEach var="h" begin="${hour}" end="${end - 2}" step="2">
              <div>
                <input type="radio" class="btn-check" name="rentTime" id="time${h}" value="${h}:00 ~ ${h+2}:00">
                <label class="btn btn-outline-primary" for="time${h}">${h}:00 ~ ${h+2}:00</label>
              </div>
            </c:forEach>
          </div>
          <div class="d-grid gap-2">
            <c:choose>
              <c:when test="${empty loginUser}">
                <button type="button" class="btn btn-secondary" disabled>로그인 후 대여 가능</button>
              </c:when>
              <c:otherwise>
                <button type="submit" class="btn btn-primary">대여 예약하기</button>
              </c:otherwise>
            </c:choose>
            <a href="${pageContext.request.contextPath}/stadium/list" class="btn btn-outline-secondary">구장 목록으로</a>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
