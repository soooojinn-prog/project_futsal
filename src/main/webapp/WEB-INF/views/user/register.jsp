<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="회원가입"/>
  <jsp:param name="menu" value="user"/>
  <jsp:param name="pageCss" value="user.css"/>
</jsp:include>
<script>
  function validateForm() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    if (password !== confirmPassword) {
      alert("비밀번호가 일치하지 않습니다!");
      return false;
    }
    const xhr = new XMLHttpRequest();
    xhr.open("GET", "${pageContext.request.contextPath}/user/check-email?email=" + encodeURIComponent(email), false);
    xhr.send();
    if (xhr.status === 200) {
      const emailExists = xhr.responseText === "true";
      if (emailExists) {
        alert("이미 사용 중인 이메일입니다!");
        return false;
      }
    }
    return true;
  }
</script>
<div class="auth-wrapper">
  <div class="auth-card card">
    <div class="card-header bg-primary text-white">
      <h4 class="mb-0 fw-bold">회원가입</h4>
    </div>
    <div class="card-body p-4">
      <form action="${pageContext.request.contextPath}/user/register" method="post" onsubmit="return validateForm()">
        <div class="mb-3">
          <label for="email" class="form-label">이메일</label>
          <input type="email" class="form-control" id="email" name="email" required>
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">비밀번호</label>
          <input type="password" class="form-control" id="password" name="password" required>
        </div>
        <div class="mb-3">
          <label for="confirmPassword" class="form-label">비밀번호 확인</label>
          <input type="password" class="form-control" id="confirmPassword" name="confirmPassword" required>
        </div>
        <div class="mb-3">
          <label for="nickname" class="form-label">닉네임</label>
          <input type="text" class="form-control" id="nickname" name="nickname" required>
        </div>
        <div class="mb-3">
          <label class="form-label">성별</label>
          <div class="d-flex gap-4">
            <div class="form-check">
              <input class="form-check-input" type="radio" name="gender" value="MALE" id="genderMale" required>
              <label class="form-check-label" for="genderMale">남성</label>
            </div>
            <div class="form-check">
              <input class="form-check-input" type="radio" name="gender" value="FEMALE" id="genderFemale" required>
              <label class="form-check-label" for="genderFemale">여성</label>
            </div>
          </div>
        </div>
        <div class="mb-3">
          <label for="preferredPosition" class="form-label">선호 포지션</label>
          <select class="form-select" id="preferredPosition" name="preferredPosition">
            <option value="">선택안함</option>
            <option value="GK">골키퍼 (GK)</option>
            <option value="DF">수비수 (DF)</option>
            <option value="MF">미드필더 (MF)</option>
            <option value="FW">공격수 (FW)</option>
          </select>
        </div>
        <div class="mb-4">
          <label for="introduction" class="form-label">자기소개 (선택사항)</label>
          <textarea class="form-control" id="introduction" name="introduction" rows="3" placeholder="자기소개를 입력하세요..."></textarea>
        </div>
        <div class="d-grid">
          <button type="submit" class="btn btn-primary btn-lg">회원가입하기</button>
        </div>
      </form>
    </div>
    <div class="card-footer text-center">
      <span class="text-muted small">이미 계정이 있으신가요?</span>
      <a href="${pageContext.request.contextPath}/user/login" class="ms-2 small">로그인하기</a>
    </div>
  </div>
</div>
<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
