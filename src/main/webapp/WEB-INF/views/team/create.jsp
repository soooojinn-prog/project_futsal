<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="팀 생성"/>
  <jsp:param name="menu" value="team"/>
  <jsp:param name="pageCss" value="team-stadium.css"/>
</jsp:include>
<script>
  function gradeToText(value) {
    switch (value) {
      case "0": return "입문";
      case "1": return "초보";
      case "2": return "중수";
      case "3": return "고수";
      default: return "";
    }
  }
  function confirmCreate() {
    const isLogin = ${loginUser != null ? 'true' : 'false'};
    if (!isLogin) {
      alert("로그인 후 생성 가능합니다.");
      return false;
    }
    const teamName = document.querySelector('input[name="teamName"]').value;
    const gender = document.querySelector('input[name="gender"]:checked');
    const minGradeValue = document.querySelector('select[name="minGrade"]').value;
    const maxGradeValue = document.querySelector('select[name="maxGrade"]').value;
    const region = document.querySelector('select[name="region"]').value;
    const introduction = document.querySelector('textarea[name="introduction"]').value;
    if (!teamName || !gender) {
      alert("팀 이름과 성별은 필수입니다.");
      return false;
    }
    let genderText = gender.value === "MALE" ? "남성" : gender.value === "FEMALE" ? "여성" : "혼성";
    const minGrade = gradeToText(minGradeValue);
    const maxGrade = gradeToText(maxGradeValue);
    const isConfirmed = confirm(
        "생성하려는 팀 : " + teamName + " 팀\n\n" +
        "성별 : " + genderText + "\n" +
        "최소 등급 : " + minGrade + "\n" +
        "최대 등급 : " + maxGrade + "\n" +
        "지역 : " + region + "\n" +
        "소개 : " + introduction + "\n\n" +
        "위 정보가 맞습니까?"
    );
    if (isConfirmed) {
      alert(teamName + " 팀이 생성되었습니다!");
      return true;
    }
    return false;
  }
</script>
<div class="page-hero">
  <h2>팀 생성</h2>
  <div class="page-hero-bar"></div>
</div>
<div class="row justify-content-center">
  <div class="col-lg-6">
    <div class="card shadow-sm">
      <div class="card-body p-4">
        <form action="${pageContext.request.contextPath}/team/create" method="post" onsubmit="return confirmCreate()">
          <div class="mb-3">
            <label class="form-label">팀 이름</label>
            <input type="text" name="teamName" class="form-control" required>
          </div>
          <div class="mb-3">
            <label class="form-label">성별</label>
            <div class="d-flex gap-3">
              <div class="form-check">
                <input class="form-check-input" type="radio" name="gender" value="BOTH" id="genderBoth">
                <label class="form-check-label" for="genderBoth">혼성</label>
              </div>
              <div class="form-check">
                <input class="form-check-input" type="radio" name="gender" value="MALE" id="genderMale">
                <label class="form-check-label" for="genderMale">남성</label>
              </div>
              <div class="form-check">
                <input class="form-check-input" type="radio" name="gender" value="FEMALE" id="genderFemale">
                <label class="form-check-label" for="genderFemale">여성</label>
              </div>
            </div>
          </div>
          <div class="row mb-3">
            <div class="col-6">
              <label class="form-label">최소 등급</label>
              <select name="minGrade" class="form-select">
                <option value="0">입문</option>
                <option value="1">초보</option>
                <option value="2">중수</option>
                <option value="3">고수</option>
              </select>
            </div>
            <div class="col-6">
              <label class="form-label">최대 등급</label>
              <select name="maxGrade" class="form-select">
                <option value="0">입문</option>
                <option value="1">초보</option>
                <option value="2">중수</option>
                <option value="3">고수</option>
              </select>
            </div>
          </div>
          <div class="mb-3">
            <label class="form-label">지역</label>
            <select name="region" class="form-select">
              <option>서울</option>
              <option>경기</option>
              <option>강원</option>
              <option>충청</option>
              <option>전라</option>
              <option>경상</option>
              <option>제주</option>
            </select>
          </div>
          <div class="mb-4">
            <label class="form-label">팀 소개</label>
            <textarea name="introduction" class="form-control" rows="4"></textarea>
          </div>
          <div class="d-grid gap-2">
            <button type="submit" class="btn btn-primary">생성하기</button>
            <a href="${pageContext.request.contextPath}/team" class="btn btn-outline-secondary">취소</a>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
