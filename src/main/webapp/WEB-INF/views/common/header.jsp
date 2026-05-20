<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${param.title} - 렛츠풋살</title>
  <script>const contextPath = '${pageContext.request.contextPath}';</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,600;0,700;0,800;1,700&family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/bootstrap/bootstrap.min.css"/>
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/common/theme.css"/>
  <c:if test="${not empty param.pageCss}">
    <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/pages/${param.pageCss}"/>
  </c:if>
</head>
<body>
  <div class="header-accent-line"></div>
  <header>
    <div class="container py-2">
      <div class="d-flex align-items-center justify-content-between">
        <a href="${pageContext.request.contextPath}/" class="d-inline-flex align-items-center text-decoration-none">
          <img src="${pageContext.request.contextPath}/resources/image/logo/logo.png" height="42" alt="렛츠풋살 로고">
        </a>
        <div class="text-end">
          <c:choose>
            <%--@elvariable id="loginUser" type="io.github.wizwix.letsfutsal.dto.UserDTO"--%>
            <c:when test="${not empty loginUser}">
              <span class="small">${loginUser.nickname}님 환영합니다</span>
              <span class="mx-2" style="color:var(--border)">|</span>
              <a href="${pageContext.request.contextPath}/user/logout" class="small">로그아웃</a>
              <span class="mx-2" style="color:var(--border)">|</span>
              <a href="${pageContext.request.contextPath}/user/mypage" class="small">마이페이지</a>
            </c:when>
            <c:otherwise>
              <a href="${pageContext.request.contextPath}/user/login" class="small">로그인</a>
              <span class="mx-2" style="color:var(--border)">|</span>
              <a href="${pageContext.request.contextPath}/user/register" class="small">회원가입</a>
            </c:otherwise>
          </c:choose>
        </div>
      </div>
    </div>
  </header>
  <nav>
    <div class="container">
      <ul class="nav justify-content-center py-2">
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'match'   ? 'active' : ''}" href="${pageContext.request.contextPath}/match"><span class="nav-emoji">⚽</span> 매치</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'team'    ? 'active' : ''}" href="${pageContext.request.contextPath}/team"><span class="nav-emoji">👥</span> 팀</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'stadium' ? 'active' : ''}" href="${pageContext.request.contextPath}/stadium"><span class="nav-emoji">🏟️</span> 구장</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'rank'    ? 'active' : ''}" href="${pageContext.request.contextPath}/rank"><span class="nav-emoji">🏆</span> 랭킹</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'board'   ? 'active' : ''}" href="${pageContext.request.contextPath}/free"><span class="nav-emoji">📋</span> 게시판</a>
        </li>
        <c:if test="${not empty loginUser}">
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'coordinator' ? 'active' : ''}" href="${pageContext.request.contextPath}/ai/coordinator"><span class="nav-emoji">🤖</span> AI 코디네이터</a>
        </li>
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'pose' ? 'active' : ''}" href="${pageContext.request.contextPath}/ai/pose"><span class="nav-emoji">🏃</span> 자세 분석</a>
        </li>
        </c:if>
      </ul>
      <style>
        /* 네비 메뉴 active/hover 시에도 이모지는 원래 색상 유지 */
        .nav-emoji {
          color: initial !important;
          -webkit-text-fill-color: initial !important;
          text-shadow: none !important;
          font-style: normal;
        }
      </style>
    </div>
  </nav>

  <%-- AI 챗봇 위젯 (로그인 유저에게만 표시) --%>
  <c:if test="${not empty loginUser}">
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

  <main class="container py-4">
