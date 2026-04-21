<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="마이페이지"/>
  <jsp:param name="menu" value="user"/>
  <jsp:param name="pageCss" value="user.css"/>
</jsp:include>
<c:choose>
  <c:when test="${not empty sessionScope.loginUser}">
    <div class="page-hero">
      <h2>마이페이지</h2>
      <div class="page-hero-bar"></div>
    </div>
    <div class="row g-4">
      <div class="col-lg-4">
        <div class="profile-card">
          <div class="profile-avatar">${loginUser.nickname.charAt(0)}</div>
          <div class="profile-nickname">${loginUser.nickname}</div>
          <div class="profile-badges">
            <span class="grade-badge">
              <c:choose>
                <c:when test="${loginUser.grade==0}">입문</c:when>
                <c:when test="${loginUser.grade==1}">초보</c:when>
                <c:when test="${loginUser.grade==2}">중수</c:when>
                <c:otherwise>고수</c:otherwise>
              </c:choose>
            </span>
          </div>
          <div class="point-highlight">${loginUser.point} <span>P</span></div>
          <table class="profile-table mt-3">
            <tr>
              <th>이메일</th>
              <td>${loginUser.email}</td>
            </tr>
            <tr>
              <th>성별</th>
              <td>
                <c:choose>
                  <c:when test="${loginUser.gender=='MALE'}">남성</c:when>
                  <c:when test="${loginUser.gender=='FEMALE'}">여성</c:when>
                  <c:otherwise>${loginUser.gender}</c:otherwise>
                </c:choose>
              </td>
            </tr>
            <tr>
              <th>가입일</th>
              <td>${loginUser.createdAt}</td>
            </tr>
          </table>
        </div>
      </div>
      <div class="col-lg-8">
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0 fw-bold">정보 수정</h5>
          </div>
          <div class="card-body p-4">
            <form action="${pageContext.request.contextPath}/user/update" method="post">
              <input type="hidden" name="userId" value="${loginUser.userId}">
              <div class="mb-3">
                <label for="nickname" class="form-label">닉네임</label>
                <input type="text" class="form-control" id="nickname" name="nickname" value="${loginUser.nickname}" required>
              </div>
              <div class="mb-3">
                <label for="password" class="form-label">새 비밀번호</label>
                <input type="password" class="form-control" id="password" name="password" placeholder="변경하지 않으려면 비워두세요">
                <div class="form-text text-muted">변경 시에만 입력하세요.</div>
              </div>
              <div class="mb-3">
                <label for="preferredPosition" class="form-label">선호 포지션</label>
                <select class="form-select" id="preferredPosition" name="preferredPosition">
                  <option value="" ${empty loginUser.preferredPosition ? 'selected' : ''}>선택안함</option>
                  <option value="Goalkeeper" ${loginUser.preferredPosition == 'Goalkeeper' ? 'selected' : ''}>Goalkeeper (GK)</option>
                  <option value="Defender" ${loginUser.preferredPosition == 'Defender' ? 'selected' : ''}>Defender (DF)</option>
                  <option value="Midfielder" ${loginUser.preferredPosition == 'Midfielder' ? 'selected' : ''}>Midfielder (MF)</option>
                  <option value="Forward" ${loginUser.preferredPosition == 'Forward' ? 'selected' : ''}>Forward (FW)</option>
                </select>
              </div>
              <div class="mb-4">
                <label for="introduction" class="form-label">자기소개</label>
                <textarea class="form-control" id="introduction" name="introduction" rows="4" placeholder="자기소개를 입력하세요...">${loginUser.introduction}</textarea>
              </div>
              <div class="d-flex gap-2">
                <button type="submit" class="btn btn-primary">수정하기</button>
                <a href="${pageContext.request.contextPath}/user/logout" class="btn btn-outline-danger">로그아웃</a>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </c:when>
  <c:otherwise>
    <div class="alert alert-warning text-center py-5">
      <p class="mb-3">로그인이 필요합니다.</p>
      <a href="${pageContext.request.contextPath}/user/login" class="btn btn-primary">로그인하기</a>
    </div>
  </c:otherwise>
</c:choose>
<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
