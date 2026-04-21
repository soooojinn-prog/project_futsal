<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="로그인"/>
  <jsp:param name="menu" value="user"/>
  <jsp:param name="pageCss" value="user.css"/>
</jsp:include>
<script>
  window.onload = function () {
    var urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('error') === 'true') {
      alert("이메일 또는 비밀번호가 일치하지 않습니다!");
    }
  };
</script>
<div class="auth-wrapper">
  <div class="auth-card card shadow-sm">
    <div class="card-header bg-primary text-white">
      <h4 class="mb-0 fw-bold">로그인</h4>
    </div>
    <div class="card-body p-4">
      <form action="${pageContext.request.contextPath}/user/login" method="post">
        <div class="mb-3">
          <label for="email" class="form-label">이메일</label>
          <input type="email" class="form-control" id="email" name="email" placeholder="이메일을 입력하세요" required>
        </div>
        <div class="mb-4">
          <label for="password" class="form-label">비밀번호</label>
          <input type="password" class="form-control" id="password" name="password" placeholder="비밀번호를 입력하세요" required>
        </div>
        <div class="d-grid">
          <button type="submit" class="btn btn-primary btn-lg">로그인</button>
        </div>
      </form>
    </div>
    <div class="card-footer text-center">
      <span class="text-muted small">계정이 없으신가요?</span>
      <a href="${pageContext.request.contextPath}/user/register" class="ms-2 small">회원가입하기</a>
    </div>
  </div>
</div>
<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
