# AI UI 연동 버그 수정 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 챗봇·추천 엔진 두 AI 기능이 UI에 정상적으로 표시되도록 5가지 버그를 수정한다.

**Architecture:** (1) MyBatis 쿼리에 stadium JOIN 추가로 데이터 공백 해소 → (2) 프론트엔드 JS/JSP에서 ENUM 한글화·스타일 수정 → (3) 챗봇 위젯을 다크 테마 CSS 변수 기반으로 전면 교체.

**Tech Stack:** MyBatis XML, JSP/JSTL, Vanilla JS, Java (AiService), 사이트 다크 테마 CSS 변수(`--accent:#00C878`, `--bg-3:#161616` 등 `theme.css`에 정의됨)

---

## 발견된 버그 요약

| 우선순위 | 버그 | 영향 |
|---|---|---|
| CRITICAL | `selectMatchById`에 stadium JOIN 없음 | 추천 카드 경기장명·지역 항상 빈값 |
| HIGH | 추천 카드 `matchType` 영어 raw값 노출 | "INDIVIDUAL" 문자열이 뱃지에 표시됨 |
| HIGH | 추천 카드 등급 숫자 노출 | "0~3"이 표시됨 (입문~고수여야 함) |
| HIGH | 추천 카드 border가 theme.css에 덮어씌워짐 | 강조 테두리가 사라짐 |
| HIGH | `hr`의 `mt-4`가 `hr{margin:0!important}`에 무력화 | 추천 섹션 하단 간격 없음 |
| HIGH | `max_tokens:1024` → 답변이 잘릴 수 있음 | 긴 조언 응답 중간에 끊김 |
| HIGH | 챗봇 위젯이 흰 배경+파란색 → 다크 테마와 이질감 | 사이트 전체 디자인 불일치 |
| MED | 챗봇 패널 너비 340px 고정 | 320px 모바일에서 가로 스크롤 |
| LOW | `${loginUser.nickname}` XSS (EL 미이스케이프) | 닉네임에 HTML 삽입 시 실행 가능 |

---

## 수정 파일 목록

| 파일 | 수정 유형 | 담당 Task |
|---|---|---|
| `src/main/resources/mybatis/mapper_match.xml` | Modify L33-37 | Task 1 |
| `src/main/java/.../ai/AiService.java` | Modify L78 | Task 2 |
| `src/main/webapp/WEB-INF/views/match/list.jsp` | Modify L19-58 | Task 3 |
| `src/main/webapp/WEB-INF/views/common/header.jsp` | Modify L70-135 | Task 4 |

---

## Task 1: selectMatchById에 stadium JOIN 추가

**Files:**
- Modify: `src/main/resources/mybatis/mapper_match.xml:33-37`

이 쿼리는 `RecommendService.getRecommendedMatches`에서 각 추천 matchId별로 호출된다.
현재 `select *`만 하므로 `stadiumName`, `region`이 null이다.
`selectMatchList`(L39-72)의 JOIN 패턴을 그대로 적용한다.

- [ ] **Step 1: `selectMatchById` 쿼리 수정**

`src/main/resources/mybatis/mapper_match.xml` L33-37을 교체한다:

```xml
<select id="selectMatchById" parameterType="long" resultType="io.github.wizwix.letsfutsal.dto.MatchDTO">
  select
    m.*,
    s.name as stadiumName,
    s.region
  from letsfutsal.game_match m
  join letsfutsal.stadium s on m.stadium_id = s.stadium_id
  where m.match_id = #{matchId}
</select>
```

- [ ] **Step 2: 수동 검증**

서버를 기동하고 브라우저에서 매치 목록 페이지(`/match`)에 로그인 상태로 접속한다.
AI 추천 섹션 카드에 **경기장명과 지역이 표시**되는지 확인한다.
(이전: "경기장 미정", "", 이후: 실제 경기장명·지역)

- [ ] **Step 3: 커밋**

```bash
git add src/main/resources/mybatis/mapper_match.xml
git commit -m "fix: selectMatchById에 stadium JOIN 추가 — 추천 카드 경기장명/지역 null 해소"
```

---

## Task 2: max_tokens 1024 → 2048으로 증가

**Files:**
- Modify: `src/main/java/io/github/wizwix/letsfutsal/ai/AiService.java:78`

1024 토큰은 한국어 기준 약 600-800자로, 긴 전술 조언이나 훈련 계획 응답이 중간에 잘린다.
2048은 약 1400자 분량으로 대부분의 풋살 조언 응답에 충분하다.

- [ ] **Step 1: `buildRequestBody`의 `max_tokens` 수정**

`AiService.java` L78을 수정한다. 변경 전:

```java
return String.format(
    "{\"model\":\"claude-sonnet-4-6\",\"max_tokens\":1024,\"system\":%s,\"messages\":[{\"role\":\"user\",\"content\":%s}]}",
    systemJson, messageJson);
```

변경 후:

```java
return String.format(
    "{\"model\":\"claude-sonnet-4-6\",\"max_tokens\":2048,\"system\":%s,\"messages\":[{\"role\":\"user\",\"content\":%s}]}",
    systemJson, messageJson);
```

- [ ] **Step 2: 수동 검증**

챗봇 위젯에서 "풋살 훈련 계획을 2주 단위로 자세히 짜줘"처럼 긴 답변을 유도하는 질문을 입력해
답변이 중간에 끊기지 않고 완결되는지 확인한다.

- [ ] **Step 3: 커밋**

```bash
git add src/main/java/io/github/wizwix/letsfutsal/ai/AiService.java
git commit -m "fix: Claude API max_tokens 1024 → 2048 — 긴 답변 잘림 방지"
```

---

## Task 3: 추천 카드 UI 수정

**Files:**
- Modify: `src/main/webapp/WEB-INF/views/match/list.jsp:19-58`

수정 항목:
1. `matchType` 한글 변환 (`INDIVIDUAL`→개인, `TEAM`→팀, `RENT`→대여)
2. 등급 숫자 한글 변환 (`0`→입문, `1`→초보, `2`→중수, `3`→고수)
3. 카드 border: `border-primary`(Bootstrap, `!important`에 덮어씌워짐) → 인라인 `!important`로 강제
4. `<hr class="mt-4">`: theme.css의 `hr { margin:0 !important; }`에 무력화됨 → `<div>` 구분선으로 교체

- [ ] **Step 1: 추천 섹션 전체 교체 (list.jsp L19-58)**

L19의 `<%-- AI 추천 섹션 --%>` 블록 전체를 아래로 교체한다:

```jsp
<%-- AI 추천 섹션 (로그인 유저에게만 표시) --%>
<c:if test="${not empty loginUser}">
  <div id="ai-recommend-section" class="mb-4" style="display:none;">
    <div class="d-flex align-items-center gap-2 mb-3">
      <span style="font-size:20px;">&#x26BD;</span>
      <h5 class="mb-0 fw-bold">AI 추천 매치</h5>
      <span class="badge" style="background:var(--accent);color:#000;font-size:11px;">FOR YOU</span>
    </div>
    <div id="ai-recommend-list" class="row g-3">
      <div class="col-12 text-center text-muted py-3">
        <div class="spinner-border spinner-border-sm me-2" role="status"></div>
        AI가 맞춤 매치를 분석 중입니다...
      </div>
    </div>
    <div style="border-top:1px solid var(--border);margin-top:1.5rem;margin-bottom:0;"></div>
  </div>
  <script>
    function matchTypeLabel(type) {
      var map = { 'INDIVIDUAL': '개인', 'TEAM': '팀', 'RENT': '대여' };
      return map[type] || '매치';
    }
    function gradeLabel(g) {
      var map = { 0: '입문', 1: '초보', 2: '중수', 3: '고수' };
      return map[g] !== undefined ? map[g] : g;
    }
    function matchTypeBadgeColor(type) {
      var map = { 'INDIVIDUAL': 'var(--badge-individual)', 'TEAM': 'var(--badge-team)', 'RENT': 'var(--badge-rent)' };
      return map[type] || 'var(--accent)';
    }

    fetch(contextPath + '/ai/recommend/matches')
      .then(function(res) { return res.json(); })
      .then(function(matches) {
        if (!matches || matches.length === 0) return;
        var section = document.getElementById('ai-recommend-section');
        var list = document.getElementById('ai-recommend-list');
        section.style.display = 'block';
        list.innerHTML = matches.map(function(m) {
          return '<div class="col-md-4">'
            + '<a href="' + contextPath + '/match/' + m.matchId + '" class="text-decoration-none">'
            + '<div class="card h-100" style="border:2px solid var(--accent-border) !important;">'
            + '<div class="card-body">'
            + '<div class="d-flex justify-content-between align-items-start mb-2">'
            + '<span class="badge" style="background:' + matchTypeBadgeColor(m.matchType) + ';color:#000;">'
            + matchTypeLabel(m.matchType) + '</span>'
            + '<small class="text-muted">' + (m.region || '') + '</small>'
            + '</div>'
            + '<p class="mb-1 fw-bold" style="color:var(--text);">' + (m.stadiumName || '경기장 미정') + '</p>'
            + '<small class="text-muted">' + (m.matchDate || '') + ' | 등급 '
            + gradeLabel(m.minGrade) + '~' + gradeLabel(m.maxGrade) + '</small>'
            + '</div></div></a></div>';
        }).join('');
      })
      .catch(function() {});
  </script>
</c:if>
```

- [ ] **Step 2: 수동 검증**

매치 목록 페이지에서 추천 섹션을 확인한다:
- 뱃지에 "개인" / "팀" / "대여"가 표시되는지
- 등급이 "0~3" 대신 "입문~고수"로 표시되는지
- 카드 테두리가 녹색(accent-border)으로 표시되는지
- 추천 섹션 아래 구분선과 하단 페이지 히어로 사이에 간격이 생겼는지

- [ ] **Step 3: 커밋**

```bash
git add src/main/webapp/WEB-INF/views/match/list.jsp
git commit -m "fix: 추천 카드 matchType 한글화, 등급 라벨, border 스타일, hr 간격 수정"
```

---

## Task 4: 챗봇 위젯 다크 테마 + 모바일 반응형

**Files:**
- Modify: `src/main/webapp/WEB-INF/views/common/header.jsp:70-135`

현재 위젯은 흰 배경(`#fff`) + 파란색(`#2563eb`)으로 사이트 다크 테마와 완전히 충돌한다.
theme.css의 CSS 변수(`--bg-3`, `--accent`, `--border`, `--text` 등)를 모두 사용해 통일한다.
모바일에서 패널 너비가 화면을 넘치는 문제도 `min(340px, calc(100vw - 48px))`으로 수정한다.
`${loginUser.nickname}` XSS도 함께 수정한다(`<c:out>` 적용).

- [ ] **Step 1: 챗봇 위젯 블록 전체 교체 (header.jsp L70-135)**

L70의 `<%-- AI 챗봇 위젯 --%>` 블록 전체를 아래로 교체한다:

```jsp
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
      .then(function(data) { addBubble(data.message || data.error || '오류가 발생했습니다.', false); })
      .catch(function() { addBubble('연결 오류가 발생했습니다.', false); });
    }
  </script>
</c:if>
```

- [ ] **Step 2: 수동 검증**

1. 브라우저에서 매치 목록 페이지에 로그인 상태로 접속한다.
2. 우하단 ⚽ 버튼을 클릭해 챗봇 패널을 연다.
3. 패널 배경이 다크(#161616), 헤더가 녹색 그라디언트, 입력창이 다크 배경으로 표시되는지 확인한다.
4. 메시지를 보내서 사용자 말풍선(녹색 배경, 검정 텍스트)과 봇 말풍선(어두운 배경, 밝은 텍스트)이 올바르게 표시되는지 확인한다.
5. 모바일 크기(Chrome DevTools → 375px)에서 패널이 화면 내에 들어오는지 확인한다.
6. 닉네임 환영 메시지가 정상적으로 표시되는지 확인한다.

- [ ] **Step 3: 커밋**

```bash
git add src/main/webapp/WEB-INF/views/common/header.jsp
git commit -m "fix: 챗봇 위젯 다크 테마 통합, 모바일 반응형, XSS 수정"
```

---

## 최종 확인 체크리스트

- [ ] 매치 목록 페이지 추천 카드에 **경기장명과 지역이 표시**된다
- [ ] 추천 카드 뱃지에 **"개인" / "팀" / "대여"**가 표시된다
- [ ] 추천 카드 등급이 **"입문~고수"** 형식으로 표시된다
- [ ] 추천 카드 테두리가 **녹색(--accent-border)**으로 표시된다
- [ ] 추천 섹션 하단에 **구분선 간격**이 생겼다
- [ ] 챗봇 패널이 **다크 배경(--bg-3)**으로 표시된다
- [ ] 챗봇 헤더/버튼이 **녹색 그라디언트(--accent)**로 표시된다
- [ ] 챗봇 입력창이 **다크 배경(--bg-4)**으로 표시된다
- [ ] 모바일(375px)에서 챗봇 패널이 **화면 내에 들어온다**
- [ ] 챗봇에서 긴 답변 요청 시 **응답이 잘리지 않는다**
