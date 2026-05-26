<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib uri="jakarta.tags.core" prefix="c" %>
<jsp:include page="../common/header.jsp">
  <jsp:param name="title" value="AI 매치 코디네이터"/>
  <jsp:param name="menu" value="coordinator"/>
</jsp:include>

<style>
    :root {
      --accent: #00d4a3;
      --accent-dark: #00a37e;
      --bg-1: #0a0a0a;
      --bg-2: #121212;
      --bg-3: #1a1a1a;
      --bg-4: #232323;
      --border: rgba(255,255,255,0.08);
      --text: #f5f5f5;
      --text-muted: #a0a0a0;
    }

    body { background: var(--bg-1); color: var(--text); }

    .coord-hero { max-width: 880px; margin: 32px auto 16px; padding: 0 24px; }
    .coord-hero h1 {
      font-size: 28px; font-weight: 700; margin-bottom: 8px;
      background: linear-gradient(135deg, var(--accent), #6cf);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    /* h1 그라데이션이 이모지까지 칠하지 않도록 분리 — span으로 원래 색상 유지 */
    .coord-hero h1 .hero-emoji {
      -webkit-text-fill-color: initial; color: initial; background: none;
      -webkit-background-clip: initial; background-clip: initial;
      margin-right: 8px; font-style: normal;
    }
    .coord-hero p { color: var(--text-muted); font-size: 15px; line-height: 1.6; }

    .coord-wrap { max-width: 880px; margin: 0 auto 60px; padding: 0 24px; }

    .input-card {
      background: linear-gradient(135deg, var(--bg-3), var(--bg-2));
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }
    .input-card label {
      display: block; font-size: 13px; color: var(--text-muted);
      margin-bottom: 8px; font-weight: 500;
    }
    .coord-input {
      width: 100%; min-height: 96px; padding: 14px 16px;
      border-radius: 12px; border: 1px solid var(--border);
      background: var(--bg-1); color: var(--text);
      font-size: 15px; font-family: inherit; resize: vertical;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    .coord-input:focus {
      outline: none; border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(0,212,163,0.15);
    }
    .coord-examples { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    .example-chip {
      padding: 6px 12px; border-radius: 20px;
      background: var(--bg-4); color: var(--text-muted);
      font-size: 13px; cursor: pointer;
      border: 1px solid var(--border);
      transition: all 0.15s;
    }
    .example-chip:hover {
      background: var(--accent); color: #000; border-color: var(--accent);
    }

    .btn-coord {
      margin-top: 16px; padding: 12px 24px;
      border-radius: 12px; border: none;
      font-weight: 600; cursor: pointer;
      font-size: 15px;
      transition: transform 0.1s, box-shadow 0.2s;
    }
    .btn-primary-coord {
      background: linear-gradient(135deg, var(--accent), var(--accent-dark));
      color: #000;
      box-shadow: 0 4px 12px rgba(0,212,163,0.3);
    }
    .btn-primary-coord:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(0,212,163,0.4);
    }
    .btn-primary-coord:disabled { opacity: 0.5; cursor: not-allowed; }

    .preview-area { margin-top: 32px; }
    .preview-title {
      font-size: 20px; font-weight: 700; margin-bottom: 16px;
      display: flex; align-items: center; gap: 8px;
    }

    .warning-card {
      background: rgba(255,193,7,0.08);
      border: 1px solid rgba(255,193,7,0.25);
      border-radius: 12px;
      padding: 12px 16px;
      margin-bottom: 16px;
      font-size: 14px;
      color: #ffd966;
    }

    .match-card {
      background: linear-gradient(135deg, var(--bg-3), var(--bg-2));
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      margin-bottom: 12px;
      transition: border-color 0.2s, transform 0.15s;
    }
    .match-card:hover { border-color: rgba(0,212,163,0.3); transform: translateY(-1px); }

    .match-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
    .match-stage {
      padding: 4px 10px; border-radius: 6px;
      font-size: 12px; font-weight: 700;
      background: rgba(0,212,163,0.15); color: var(--accent);
      letter-spacing: 0.5px;
    }
    .match-remove {
      background: transparent;
      border: 1px solid rgba(255,77,77,0.4);
      color: #ff6b6b;
      padding: 4px 12px;
      border-radius: 6px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .match-remove:hover { background: rgba(255,77,77,0.15); }

    .match-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; font-size: 14px; }
    .match-row .label {
      min-width: 90px; color: var(--text-muted);
      display: flex; align-items: center; gap: 6px;
    }
    .match-row input[type="datetime-local"] {
      padding: 6px 10px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg-1);
      color: var(--text);
      font-family: inherit;
      font-size: 14px;
    }
    .match-row input[type="datetime-local"]:focus {
      outline: none; border-color: var(--accent);
    }

    .btn-confirm {
      width: 100%; margin-top: 24px; padding: 14px;
      background: linear-gradient(135deg, var(--accent), var(--accent-dark));
      color: #000; border: none; border-radius: 12px;
      font-weight: 700; font-size: 16px; cursor: pointer;
      box-shadow: 0 4px 16px rgba(0,212,163,0.3);
      transition: transform 0.1s, box-shadow 0.2s;
    }
    .btn-confirm:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 8px 20px rgba(0,212,163,0.4);
    }
    .btn-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

    .result-card {
      background: linear-gradient(135deg, rgba(0,212,163,0.12), rgba(0,212,163,0.04));
      border: 1px solid rgba(0,212,163,0.3);
      border-radius: 14px;
      padding: 24px;
      text-align: center;
      margin-top: 24px;
    }
    .result-card h3 { font-size: 20px; color: var(--accent); margin-bottom: 12px; }

    .loading-spinner {
      display: inline-block;
      width: 14px; height: 14px;
      border: 2px solid rgba(0,0,0,0.2);
      border-top-color: #000;
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
      margin-right: 8px;
      vertical-align: middle;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* ───── 토너먼트 대진표 ───── */
    .bracket-card {
      background: linear-gradient(135deg, var(--bg-3), var(--bg-2));
      border: 1px solid var(--border); border-radius: 12px;
      padding: 18px; margin-bottom: 16px; overflow-x: auto;
    }
    .bracket-title { font-size: 14px; font-weight: 600; margin-bottom: 12px;
                      color: var(--text); }
    .bracket-wrap { display: flex; gap: 24px; min-width: max-content; padding: 4px 0; }
    .bracket-round { display: flex; flex-direction: column;
                      justify-content: space-around; gap: 8px;
                      position: relative; min-width: 160px; }
    .bracket-round-title { font-size: 11px; color: var(--text-muted);
                            text-transform: uppercase; letter-spacing: 0.5px;
                            margin-bottom: 6px; text-align: center; font-weight: 600; }
    .bracket-match {
      background: var(--bg-1); border: 1px solid var(--border);
      border-radius: 8px; padding: 8px 12px; font-size: 12px;
      min-width: 140px; position: relative;
    }
    .bracket-match.has-winner { border-color: rgba(0,212,163,0.4); }
    .bracket-team { display: flex; justify-content: space-between; padding: 3px 0;
                     color: var(--text); }
    .bracket-team.team-b { border-top: 1px dashed var(--border); padding-top: 5px; margin-top: 3px; }
    .bracket-team .vs-sep { color: var(--text-muted); }
    .bracket-tbd { color: var(--text-muted); font-style: italic; }
    .bracket-stage { font-size: 10px; color: var(--accent); font-weight: 700;
                      display: block; margin-bottom: 4px;
                      text-transform: uppercase; letter-spacing: 0.5px; }

    /* ───── 모바일 반응형 ───── */
    @media (max-width: 768px) {
      .coord-hero { margin: 20px auto 8px; padding: 0 16px; }
      .coord-hero h1 { font-size: 22px; }
      .coord-hero p { font-size: 13px; }
      .coord-wrap { padding: 0 16px 40px; }
      .input-card { padding: 16px; border-radius: 12px; }
      .preview-area, .result-card { padding: 16px; }
      .match-card { padding: 14px; }
      .bracket-card { padding: 12px; }
      .bracket-wrap { gap: 14px; }
      .bracket-round { min-width: 130px; }
      .bracket-match { min-width: 120px; padding: 6px 10px; }
    }
  </style>

<section class="coord-hero">
  <h1><span class="hero-emoji">🤖</span>AI 매치 코디네이터</h1>
  <p>자연어 한 줄로 풋살 매치 또는 토너먼트를 자동으로 기획해 드려요.<br>
    경기장 검색부터 일정 조율까지 — AI가 알아서 준비합니다.</p>
</section>

<main class="coord-wrap">
  <div class="input-card">
    <label>💬 어떤 매치를 잡고 싶으신가요?</label>
    <textarea id="userInput" class="coord-input"
      placeholder="예) 이번 주말 강남에서 매치 잡아줘"></textarea>

    <div class="coord-examples">
      <span class="example-chip" data-example="이번 주말 강남에서 매치 잡아줘">⚽ 이번 주말 강남 매치</span>
      <span class="example-chip" data-example="다음 주 일요일 4팀 토너먼트 기획해줘">🏆 4팀 토너먼트</span>
      <span class="example-chip" data-example="다음 주 토요일 서울 매치 추천해줘">📅 다음 주 토요일</span>
    </div>

    <button id="runBtn" class="btn-coord btn-primary-coord">✨ AI에게 맡기기</button>
  </div>

  <div id="proposalArea" class="preview-area" style="display:none">
    <h2 class="preview-title">📋 AI가 준비한 미리보기</h2>
    <div id="warningsBox" class="warning-card" style="display:none"></div>
    <div id="bracketArea" style="display:none"></div>
    <div id="matchList"></div>
    <button id="confirmBtn" class="btn-confirm">✅ 이대로 매치 만들기</button>
  </div>

  <div id="resultArea" style="display:none" class="result-card"></div>
</main>

<script>
  window.AGENT_CTX = '${pageContext.request.contextPath}';
</script>
<script src="${pageContext.request.contextPath}/resources/script/agent_coordinator.js"></script>
