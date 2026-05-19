<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib uri="jakarta.tags.core" prefix="c" %>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>AI 매치 코디네이터</title>
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/css/common.css">
  <style>
    .coordinator-wrap { max-width: 800px; margin: 0 auto; padding: 24px; }
    .input-box { display: flex; flex-direction: column; gap: 8px; padding: 16px; border-radius: 12px;
                  border: 1px solid var(--border, #333); background: var(--bg-3, #1a1a1a); }
    .match-card { border: 1px solid var(--border, #333); border-radius: 8px; padding: 12px; margin: 8px 0; background: var(--bg-4, #222); }
    .match-card label { display: inline-block; min-width: 80px; opacity: 0.7; font-size: 13px; }
    .stage-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;
                   background: var(--accent, #3aa); color: #000; }
    .warning-box { padding: 12px; border-radius: 8px; background: rgba(255, 200, 0, 0.1); border: 1px solid rgba(255, 200, 0, 0.3); margin-bottom: 12px; }
    .result-box { padding: 12px; border-radius: 8px; background: rgba(0, 200, 100, 0.15); border: 1px solid rgba(0, 200, 100, 0.4); margin-top: 16px; }
    button.coord-btn { padding: 10px 16px; border-radius: 8px; border: none; cursor: pointer; font-weight: 600; }
    button.primary { background: var(--accent, #3aa); color: #000; }
    button.success { background: #2a8; color: #fff; }
    button.danger { background: #c33; color: #fff; padding: 4px 10px; font-size: 12px; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    textarea.coord-input { width: 100%; min-height: 80px; padding: 10px; border-radius: 8px;
                            border: 1px solid var(--border, #333); background: var(--bg-2, #0f0f0f); color: var(--text, #eee); }
  </style>
</head>
<body>
<jsp:include page="/WEB-INF/views/common/header.jsp"/>

<main class="coordinator-wrap">
  <h2>🤖 AI 매치 코디네이터</h2>
  <p style="opacity:0.7">자연어로 매치 또는 토너먼트 요청을 입력하세요.</p>

  <div class="input-box">
    <textarea id="userInput" class="coord-input"
      placeholder="예: 이번 주말 강남에서 4팀 토너먼트 잡아줘"></textarea>
    <div>
      <button id="runBtn" class="coord-btn primary">에이전트 실행</button>
    </div>
  </div>

  <div id="proposalArea" style="display:none; margin-top:24px;">
    <h3>📋 미리보기</h3>
    <div id="warningsBox" class="warning-box" style="display:none"></div>
    <div id="matchList"></div>
    <button id="confirmBtn" class="coord-btn success">✅ 매치 확정 (DB 저장)</button>
  </div>

  <div id="resultArea" style="display:none" class="result-box"></div>
</main>

<script>
  window.AGENT_CTX = '${pageContext.request.contextPath}';
</script>
<script src="${pageContext.request.contextPath}/resources/script/agent_coordinator.js"></script>
</body>
</html>
