<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="title" value="랭킹"/>
  <jsp:param name="menu" value="rank"/>
  <jsp:param name="pageCss" value="rank.css"/>
</jsp:include>

<div class="page-hero">
  <h2>랭킹</h2>
  <div class="page-hero-bar"></div>
</div>

<ul class="nav nav-tabs mb-4">
  <li class="nav-item">
    <a class="nav-link ${type=='individual'?'active':''}" href="${pageContext.request.contextPath}/rank?type=individual">개인 랭킹</a>
  </li>
  <li class="nav-item">
    <a class="nav-link ${type=='team'?'active':''}" href="${pageContext.request.contextPath}/rank?type=team">팀 랭킹</a>
  </li>
  <li class="nav-item">
    <a class="nav-link ${type=='gender'?'active':''}" href="${pageContext.request.contextPath}/rank?type=gender">성별 랭킹</a>
  </li>
</ul>

<div class="card filter-card mb-4">
  <div class="card-body">
    <form class="row g-3 align-items-end" method="get" action="${pageContext.request.contextPath}/rank">
      <input type="hidden" name="type" value="${type}">
      <div class="col-auto">
        <label for="grade" class="form-label">등급</label>
        <select name="grade" id="grade" class="form-select">
          <option value="-1" ${selectedGrade==-1?'selected':''}>전체</option>
          <option value="0"  ${selectedGrade==0 ?'selected':''}>입문</option>
          <option value="1"  ${selectedGrade==1 ?'selected':''}>초보</option>
          <option value="2"  ${selectedGrade==2 ?'selected':''}>중수</option>
          <option value="3"  ${selectedGrade==3 ?'selected':''}>고수</option>
        </select>
      </div>
      <c:if test="${type=='individual'}">
        <div class="col-auto">
          <label for="position" class="form-label">포지션</label>
          <select name="position" id="position" class="form-select">
            <option value=""   ${empty selectedPosition?'selected':''}>전체</option>
            <option value="GK" ${selectedPosition=='GK'?'selected':''}>골키퍼 (GK)</option>
            <option value="DF" ${selectedPosition=='DF'?'selected':''}>수비수 (DF)</option>
            <option value="MF" ${selectedPosition=='MF'?'selected':''}>미드필더 (MF)</option>
            <option value="FW" ${selectedPosition=='FW'?'selected':''}>공격수 (FW)</option>
          </select>
        </div>
      </c:if>
      <c:if test="${type=='gender'}">
        <div class="col-auto">
          <label for="gender" class="form-label">성별</label>
          <select name="gender" id="gender" class="form-select">
            <option value=""       ${empty selectedGender?'selected':''}>전체</option>
            <option value="MALE"   ${selectedGender=='MALE'  ?'selected':''}>남성</option>
            <option value="FEMALE" ${selectedGender=='FEMALE'?'selected':''}>여성</option>
          </select>
        </div>
      </c:if>
      <div class="col-auto">
        <button type="submit" class="btn btn-primary">검색</button>
      </div>
    </form>
  </div>
</div>

<c:choose>
  <%-- ── 개인 랭킹 ── --%>
  <c:when test="${type=='individual'}">

    <%-- TOP 3 포디움 --%>
    <c:if test="${not empty rankings}">
      <div class="podium-section">
        <div class="podium-cards">
          <c:forEach var="user" items="${rankings}" varStatus="vs" end="2">
            <c:choose>
              <c:when test="${vs.index==0}">
                <div class="podium-card rank-1">
                  <span class="podium-crown">👑</span>
                  <span class="podium-rank-num">1</span>
                  <div class="podium-name">${user.nickname}</div>
                  <div class="podium-meta">
                    <c:choose><c:when test="${empty user.preferredPosition}">-</c:when><c:otherwise>${user.preferredPosition}</c:otherwise></c:choose>
                    &nbsp;|&nbsp;
                    <c:choose><c:when test="${user.grade==0}">입문</c:when><c:when test="${user.grade==1}">초보</c:when><c:when test="${user.grade==2}">중수</c:when><c:otherwise>고수</c:otherwise></c:choose>
                  </div>
                  <span class="podium-point">${user.point}</span>
                  <span class="podium-point-label">POINTS</span>
                </div>
              </c:when>
              <c:when test="${vs.index==1}">
                <div class="podium-card rank-2">
                  <span class="podium-crown">🥈</span>
                  <span class="podium-rank-num">2</span>
                  <div class="podium-name">${user.nickname}</div>
                  <div class="podium-meta">
                    <c:choose><c:when test="${empty user.preferredPosition}">-</c:when><c:otherwise>${user.preferredPosition}</c:otherwise></c:choose>
                    &nbsp;|&nbsp;
                    <c:choose><c:when test="${user.grade==0}">입문</c:when><c:when test="${user.grade==1}">초보</c:when><c:when test="${user.grade==2}">중수</c:when><c:otherwise>고수</c:otherwise></c:choose>
                  </div>
                  <span class="podium-point">${user.point}</span>
                  <span class="podium-point-label">POINTS</span>
                </div>
              </c:when>
              <c:otherwise>
                <div class="podium-card rank-3">
                  <span class="podium-crown">🥉</span>
                  <span class="podium-rank-num">3</span>
                  <div class="podium-name">${user.nickname}</div>
                  <div class="podium-meta">
                    <c:choose><c:when test="${empty user.preferredPosition}">-</c:when><c:otherwise>${user.preferredPosition}</c:otherwise></c:choose>
                    &nbsp;|&nbsp;
                    <c:choose><c:when test="${user.grade==0}">입문</c:when><c:when test="${user.grade==1}">초보</c:when><c:when test="${user.grade==2}">중수</c:when><c:otherwise>고수</c:otherwise></c:choose>
                  </div>
                  <span class="podium-point">${user.point}</span>
                  <span class="podium-point-label">POINTS</span>
                </div>
              </c:otherwise>
            </c:choose>
          </c:forEach>
        </div>
      </div>
    </c:if>

    <c:if test="${rankings.size() > 3}">
      <div class="rank-divider">4위 이하</div>
    </c:if>

    <div class="card shadow-sm">
      <div class="table-responsive">
        <table class="table table-hover mb-0">
          <thead class="table-dark">
            <tr>
              <th style="width:60px">순위</th>
              <th>닉네임</th>
              <th>포지션</th>
              <th>등급</th>
              <th>포인트</th>
            </tr>
          </thead>
          <tbody>
            <c:forEach var="user" items="${rankings}" varStatus="vs" begin="3">
              <tr>
                <td class="text-center rank-number">${vs.index + 1}</td>
                <td>${user.nickname}</td>
                <td><c:choose><c:when test="${empty user.preferredPosition}"><span class="text-muted">-</span></c:when><c:otherwise>${user.preferredPosition}</c:otherwise></c:choose></td>
                <td><c:choose><c:when test="${user.grade==0}">입문</c:when><c:when test="${user.grade==1}">초보</c:when><c:when test="${user.grade==2}">중수</c:when><c:when test="${user.grade==3}">고수</c:when><c:otherwise>-</c:otherwise></c:choose></td>
                <td>${user.point} P</td>
              </tr>
            </c:forEach>
            <c:if test="${empty rankings}">
              <tr><td colspan="5" class="text-center text-muted py-5">데이터가 없습니다.</td></tr>
            </c:if>
          </tbody>
        </table>
      </div>
    </div>
  </c:when>

  <%-- ── 성별 랭킹 ── --%>
  <c:when test="${type=='gender'}">
    <c:if test="${not empty rankings}">
      <div class="podium-section">
        <div class="podium-cards">
          <c:forEach var="user" items="${rankings}" varStatus="vs" end="2">
            <c:choose>
              <c:when test="${vs.index==0}">
                <div class="podium-card rank-1">
                  <span class="podium-crown">👑</span>
                  <span class="podium-rank-num">1</span>
                  <div class="podium-name">${user.nickname}</div>
                  <div class="podium-meta"><c:choose><c:when test="${user.gender=='MALE'}">남성</c:when><c:when test="${user.gender=='FEMALE'}">여성</c:when><c:otherwise>-</c:otherwise></c:choose></div>
                  <span class="podium-point">${user.point}</span>
                  <span class="podium-point-label">POINTS</span>
                </div>
              </c:when>
              <c:when test="${vs.index==1}">
                <div class="podium-card rank-2">
                  <span class="podium-crown">🥈</span>
                  <span class="podium-rank-num">2</span>
                  <div class="podium-name">${user.nickname}</div>
                  <div class="podium-meta"><c:choose><c:when test="${user.gender=='MALE'}">남성</c:when><c:when test="${user.gender=='FEMALE'}">여성</c:when><c:otherwise>-</c:otherwise></c:choose></div>
                  <span class="podium-point">${user.point}</span>
                  <span class="podium-point-label">POINTS</span>
                </div>
              </c:when>
              <c:otherwise>
                <div class="podium-card rank-3">
                  <span class="podium-crown">🥉</span>
                  <span class="podium-rank-num">3</span>
                  <div class="podium-name">${user.nickname}</div>
                  <div class="podium-meta"><c:choose><c:when test="${user.gender=='MALE'}">남성</c:when><c:when test="${user.gender=='FEMALE'}">여성</c:when><c:otherwise>-</c:otherwise></c:choose></div>
                  <span class="podium-point">${user.point}</span>
                  <span class="podium-point-label">POINTS</span>
                </div>
              </c:otherwise>
            </c:choose>
          </c:forEach>
        </div>
      </div>
    </c:if>
    <c:if test="${rankings.size() > 3}">
      <div class="rank-divider">4위 이하</div>
    </c:if>
    <div class="card shadow-sm">
      <div class="table-responsive">
        <table class="table table-hover mb-0">
          <thead class="table-dark">
            <tr><th style="width:60px">순위</th><th>닉네임</th><th>성별</th><th>등급</th><th>포인트</th></tr>
          </thead>
          <tbody>
            <c:forEach var="user" items="${rankings}" varStatus="vs" begin="3">
              <tr>
                <td class="text-center rank-number">${vs.index+1}</td>
                <td>${user.nickname}</td>
                <td><c:choose><c:when test="${user.gender=='MALE'}">남성</c:when><c:when test="${user.gender=='FEMALE'}">여성</c:when><c:otherwise>-</c:otherwise></c:choose></td>
                <td><c:choose><c:when test="${user.grade==0}">입문</c:when><c:when test="${user.grade==1}">초보</c:when><c:when test="${user.grade==2}">중수</c:when><c:when test="${user.grade==3}">고수</c:when><c:otherwise>-</c:otherwise></c:choose></td>
                <td>${user.point} P</td>
              </tr>
            </c:forEach>
            <c:if test="${empty rankings}">
              <tr><td colspan="5" class="text-center text-muted py-5">데이터가 없습니다.</td></tr>
            </c:if>
          </tbody>
        </table>
      </div>
    </div>
  </c:when>

  <%-- ── 팀 랭킹 ── --%>
  <c:otherwise>
    <c:if test="${not empty rankings}">
      <div class="podium-section">
        <div class="podium-cards">
          <c:forEach var="team" items="${rankings}" varStatus="vs" end="2">
            <c:choose>
              <c:when test="${vs.index==0}">
                <div class="podium-card rank-1">
                  <span class="podium-crown">👑</span>
                  <span class="podium-rank-num">1</span>
                  <div class="podium-name">${team.teamName}</div>
                  <div class="podium-meta">${team.region} · ${team.memberCount}명</div>
                  <span class="podium-point">${team.averagePoints}</span>
                  <span class="podium-point-label">AVG POINTS</span>
                </div>
              </c:when>
              <c:when test="${vs.index==1}">
                <div class="podium-card rank-2">
                  <span class="podium-crown">🥈</span>
                  <span class="podium-rank-num">2</span>
                  <div class="podium-name">${team.teamName}</div>
                  <div class="podium-meta">${team.region} · ${team.memberCount}명</div>
                  <span class="podium-point">${team.averagePoints}</span>
                  <span class="podium-point-label">AVG POINTS</span>
                </div>
              </c:when>
              <c:otherwise>
                <div class="podium-card rank-3">
                  <span class="podium-crown">🥉</span>
                  <span class="podium-rank-num">3</span>
                  <div class="podium-name">${team.teamName}</div>
                  <div class="podium-meta">${team.region} · ${team.memberCount}명</div>
                  <span class="podium-point">${team.averagePoints}</span>
                  <span class="podium-point-label">AVG POINTS</span>
                </div>
              </c:otherwise>
            </c:choose>
          </c:forEach>
        </div>
      </div>
    </c:if>
    <c:if test="${rankings.size() > 3}">
      <div class="rank-divider">4위 이하</div>
    </c:if>
    <div class="card shadow-sm">
      <div class="table-responsive">
        <table class="table table-hover mb-0">
          <thead class="table-dark">
            <tr><th style="width:60px">순위</th><th>팀명</th><th>지역</th><th>팀원 수</th><th>평균 포인트</th></tr>
          </thead>
          <tbody>
            <c:forEach var="team" items="${rankings}" varStatus="vs" begin="3">
              <tr>
                <td class="text-center rank-number">${vs.index+1}</td>
                <td>${team.teamName}</td>
                <td>${team.region}</td>
                <td>${team.memberCount}명</td>
                <td>${team.averagePoints} P</td>
              </tr>
            </c:forEach>
            <c:if test="${empty rankings}">
              <tr><td colspan="5" class="text-center text-muted py-5">데이터가 없습니다.</td></tr>
            </c:if>
          </tbody>
        </table>
      </div>
    </div>
  </c:otherwise>
</c:choose>

<div class="mt-4">
  <a href="${pageContext.request.contextPath}/" class="btn btn-secondary">홈으로</a>
</div>

<jsp:include page="/WEB-INF/views/common/footer.jsp"/>
