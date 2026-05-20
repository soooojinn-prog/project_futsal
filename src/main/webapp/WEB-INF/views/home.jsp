<%--@elvariable id="loginUser" type="io.github.wizwix.letsfutsal.dto.UserDTO"--%>
<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>렛츠풋살</title>
  <script>const contextPath = '${pageContext.request.contextPath}';</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/bootstrap/bootstrap.min.css"/>
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/carousel/carousel.css"/>
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/carousel/carousel.dots.css"/>
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/home/home.css"/>
</head>
<body>
  <!-- 상단 액센트 라인 -->
  <div class="header-accent-line"></div>
  <!-- 최상단 메뉴 -->
  <header class="py-2 bg-white">
    <div class="container">
      <div class="d-flex align-items-center justify-content-between">
        <!-- 로고 -->
        <a href="${pageContext.request.contextPath}/" class="d-inline-flex align-items-center text-decoration-none">
          <%--suppress CheckImageSize --%>
          <img src="${pageContext.request.contextPath}/resources/image/logo/logo.png" height="44" alt="렛츠풋살 로고">
        </a>
        <!-- 회원 링크 -->
        <div class="text-end">
          <c:choose>
            <%--@elvariable id="loginUser" type="io.github.wizwix.letsfutsal.dto.UserDTO"--%>
            <c:when test="${not empty loginUser}">
              <span class="text-muted small">${loginUser.nickname}님 환영합니다</span>
              <span class="mx-1 text-muted">|</span>
              <a href="${pageContext.request.contextPath}/user/logout" class="text-decoration-none small">로그아웃</a>
              <span class="mx-1 text-muted">|</span>
              <a href="${pageContext.request.contextPath}/user/mypage" class="text-decoration-none small">마이페이지</a>
            </c:when>
            <c:otherwise>
              <a href="${pageContext.request.contextPath}/user/login" class="text-decoration-none small">로그인</a>
              <span class="mx-1 text-muted">|</span>
              <a href="${pageContext.request.contextPath}/user/register" class="text-decoration-none small">회원가입</a>
            </c:otherwise>
          </c:choose>
        </div>
      </div>
    </div>
  </header>
  <!-- 네비게이션 바 -->
  <nav class="bg-light">
    <div class="container">
      <ul class="nav nav-pills justify-content-center py-2">
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'match'   ? 'active' : ''}" href="${pageContext.request.contextPath}/match">⚽ 매치</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'team'    ? 'active' : ''}" href="${pageContext.request.contextPath}/team">👥 팀</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'stadium' ? 'active' : ''}" href="${pageContext.request.contextPath}/stadium">🏟️ 구장</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'rank'    ? 'active' : ''}" href="${pageContext.request.contextPath}/rank">🏆 랭킹</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'board'   ? 'active' : ''}" href="${pageContext.request.contextPath}/free">📋 게시판</a>
        </li>
        <c:if test="${not empty loginUser}">
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'coordinator' ? 'active' : ''}" href="${pageContext.request.contextPath}/ai/coordinator">🤖 AI 코디네이터</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'pose' ? 'active' : ''}" href="${pageContext.request.contextPath}/ai/pose">🏃 자세 분석</a>
        </li>
        </c:if>
      </ul>
    </div>
  </nav>
  <!-- 메인 -->
  <main class="container py-4">
    <section class="container-fluid p-0 animate-fade-up visible">
      <div class="f-carousel w-100" id="banners" role="region">
        <div class="f-carousel__slide">
          <img src="${pageContext.request.contextPath}/resources/image/banner/banner_01.jpg" class="img-fluid d-block mx-auto" alt="Banner 1">
        </div>
        <div class="f-carousel__slide">
          <img src="${pageContext.request.contextPath}/resources/image/banner/banner_02.jpg" class="img-fluid d-block mx-auto" alt="Banner 2">
        </div>
        <div class="f-carousel__slide">
          <img src="${pageContext.request.contextPath}/resources/image/banner/banner_03.jpg" class="img-fluid d-block mx-auto" alt="Banner 3">
        </div>
        <div class="f-carousel__slide">
          <img src="${pageContext.request.contextPath}/resources/image/banner/banner_04.jpg" class="img-fluid d-block mx-auto" alt="Banner 4">
        </div>
        <div class="f-carousel__slide">
          <img src="${pageContext.request.contextPath}/resources/image/banner/banner_05.jpg" class="img-fluid d-block mx-auto" alt="Banner 5">
        </div>
        <div class="f-carousel__slide">
          <img src="${pageContext.request.contextPath}/resources/image/banner/banner_06.jpg" class="img-fluid d-block mx-auto" alt="Banner 6">
        </div>
      </div>
    </section>
    <!-- 임박한 매치 -->
    <div class="container my-5">
      <h3 class="section-heading mb-4">임박한 매치</h3>
      <div class="card shadow-sm mb-4 animate-fade-up" data-observe>
        <div class="card-body">
          <div id="dateFilters" class="d-flex gap-2 overflow-auto pb-3 mb-3"></div>
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label fw-semibold" for="regionFilter">지역</label>
              <select id="regionFilter" class="form-select">
                <option value="전체">전체</option>
                <option value="서울">서울</option>
                <option value="경기">경기</option>
                <option value="강원">강원</option>
                <option value="충북">충북</option>
                <option value="충남">충남</option>
                <option value="전북">전북</option>
                <option value="전남">전남</option>
                <option value="경북">경북</option>
                <option value="경남">경남</option>
                <option value="제주">제주</option>
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label fw-semibold">매치 타입</label>
              <div class="d-flex gap-2">
                <input type="radio" class="btn-check" name="matchType" id="typeAll" value="전체" checked>
                <label class="btn btn-outline-primary" for="typeAll">전체</label>
                <input type="radio" class="btn-check" name="matchType" id="typeIndiv" value="개인">
                <label class="btn btn-outline-primary" for="typeIndiv">개인</label>
                <input type="radio" class="btn-check" name="matchType" id="typeTeam" value="팀">
                <label class="btn btn-outline-primary" for="typeTeam">팀</label>
                <input type="radio" class="btn-check" name="matchType" id="typeRent" value="대여">
                <label class="btn btn-outline-primary" for="typeRent">대여</label>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div id="matchList" class="row g-4">
        <div class="text-center py-5">
          <div class="spinner-border text-primary" role="status"></div>
          <p class="mt-2">매치를 불러오는 중입니다...</p>
        </div>
      </div>
    </div>
  </main>
  <!-- 푸터 -->
  <footer class="bg-dark text-white py-4 mt-auto">
    <div class="container text-center">
      <p class="mb-1 fw-bold">LET'S FUTSAL</p>
      <p class="mb-0 small text-muted">풋살 매칭 플랫폼 &nbsp;|&nbsp; &copy; 2025 Let's Futsal. All rights reserved.</p>
    </div>
  </footer>
  <%-- AI 챗봇 위젯 (로그인 유저에게만 표시) --%>
  <c:if test="${not empty loginUser}">
    <style>
      #ai-chat-widget { --accent:#00C878; --accent-dark:#00A663; --accent-glow:rgba(0,200,120,0.22); --bg-3:#161616; --bg-4:#1E1E1E; --text:#F0F0F0; --border:rgba(255,255,255,0.07); }
    </style>
    <div id="ai-chat-widget" style="position:fixed;bottom:24px;right:24px;z-index:9999;">
      <div id="chat-panel" style="display:none;width:min(340px,calc(100vw - 48px));height:460px;background:var(--bg-3);border:1px solid var(--border);border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.5);flex-direction:column;overflow:hidden;">
        <div style="background:linear-gradient(135deg,var(--accent),var(--accent-dark));color:#000;padding:14px 18px;font-weight:700;display:flex;justify-content:space-between;align-items:center;">
          <span>&#x26BD; AI 풋살 어시스턴트</span>
          <button onclick="toggleChat()" style="background:none;border:none;color:#000;font-size:18px;cursor:pointer;">&#x2715;</button>
        </div>
        <div id="chat-messages" style="flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;background:var(--bg-3);">
          <div style="background:var(--bg-4);border:1px solid var(--border);color:var(--text);border-radius:12px 12px 12px 4px;padding:10px 14px;max-width:85%;font-size:14px;">
            안녕하세요 <c:out value="${loginUser.nickname}"/>님! 풋살 관련 무엇이든 물어보세요
          </div>
        </div>
        <div style="padding:12px;border-top:1px solid var(--border);display:flex;gap:8px;background:var(--bg-3);">
          <input id="chat-input" type="text" placeholder="메시지 입력..." maxlength="500"
                 style="flex:1;background:var(--bg-4);border:1px solid var(--border);border-radius:8px;padding:8px 12px;font-size:14px;color:var(--text);"
                 onkeydown="if(event.key==='Enter')sendMessage()">
          <button onclick="sendMessage()"
                  style="background:linear-gradient(135deg,var(--accent),var(--accent-dark));color:#000;border:none;border-radius:8px;padding:8px 14px;cursor:pointer;font-size:14px;font-weight:700;">전송</button>
        </div>
      </div>
      <button id="chat-toggle-btn" onclick="toggleChat()"
              style="display:block;width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent-dark));color:#000;border:none;font-size:24px;cursor:pointer;box-shadow:0 4px 16px var(--accent-glow);margin-top:8px;">
        &#x26BD;
      </button>
    </div>
    <script>
      var chatOpen = false;
      function toggleChat() {
        chatOpen = !chatOpen;
        var panel = document.getElementById('chat-panel');
        panel.style.display = chatOpen ? 'flex' : 'none';
        document.getElementById('chat-toggle-btn').style.display = chatOpen ? 'none' : 'block';
        if (chatOpen) document.getElementById('chat-input').focus();
      }
      function addBubble(text, isUser) {
        var el = document.createElement('div');
        el.style.cssText = isUser
          ? 'background:linear-gradient(135deg,var(--accent),var(--accent-dark));color:#000;border-radius:12px 12px 4px 12px;padding:10px 14px;max-width:85%;align-self:flex-end;font-size:14px;font-weight:600;'
          : 'background:var(--bg-4);border:1px solid var(--border);color:var(--text);border-radius:12px 12px 12px 4px;padding:10px 14px;max-width:85%;font-size:14px;';
        el.textContent = text;
        var messages = document.getElementById('chat-messages');
        messages.appendChild(el);
        messages.scrollTop = messages.scrollHeight;
      }
      function sendMessage() {
        var input = document.getElementById('chat-input');
        var msg = input.value.trim();
        if (!msg) return;
        input.value = '';
        addBubble(msg, true);
        fetch(contextPath + '/ai/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: msg})
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
          var text = data.message || data.error || '오류가 발생했습니다.';
          if (data.mode === 'RAG' && Array.isArray(data.citations) && data.citations.length) {
            var refs = data.citations.map(function(c) {
              var p = c.page ? ' p.' + c.page : '';
              return '[' + c.source + (c.section ? ' / ' + c.section : '') + p + ']';
            }).join(' ');
            text += '\n\n📚 ' + refs;
          }
          addBubble(text, false);
        })
        .catch(function() { addBubble('연결 오류가 발생했습니다.', false); });
      }
    </script>
  </c:if>
  <!-- 스크립트 -->
  <script src="${pageContext.request.contextPath}/resources/script/bootstrap/bootstrap.bundle.min.js"></script>
  <script src="${pageContext.request.contextPath}/resources/script/carousel/carousel.umd.js"></script>
  <script src="${pageContext.request.contextPath}/resources/script/carousel/carousel.autoscroll.umd.js"></script>
  <script src="${pageContext.request.contextPath}/resources/script/carousel/carousel.dots.umd.js"></script>
  <script src="${pageContext.request.contextPath}/resources/script/home/home.js"></script>
  <script>
    document.addEventListener("DOMContentLoaded", () => {
      const container = document.getElementById("banners");
      Carousel(container, { infinite: true }, { Autoscroll, Dots }).init();

      // Intersection Observer for scroll animations
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1 });

      document.querySelectorAll('[data-observe]').forEach(el => observer.observe(el));
    });
  </script>
</body>
</html>
