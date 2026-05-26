<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib uri="jakarta.tags.core" prefix="c" %>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>AI 자세 분석 — letsfutsal</title>
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/bootstrap/bootstrap.min.css">
  <style>
    :root { --accent: #00d4a3; --bg-1: #0a0a0a; --bg-3: #1a1a1a; --bg-4: #232323;
            --border: rgba(255,255,255,0.08); --text: #f5f5f5; --text-muted: #a0a0a0; }
    body { background: var(--bg-1); color: var(--text); }
    .pose-hero { max-width: 880px; margin: 32px auto 16px; padding: 0 24px; }
    .pose-hero h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px;
                     background: linear-gradient(135deg, var(--accent), #6cf);
                     -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    /* h1 그라데이션이 이모지까지 칠하지 않도록 분리 — span으로 원래 색상 유지 */
    .pose-hero h1 .hero-emoji {
      -webkit-text-fill-color: initial; color: initial; background: none;
      -webkit-background-clip: initial; background-clip: initial;
      margin-right: 8px; font-style: normal;
    }
    .pose-hero p { color: var(--text-muted); font-size: 15px; line-height: 1.6; }
    .pose-wrap { max-width: 880px; margin: 0 auto 60px; padding: 0 24px; }
    .pose-card { background: linear-gradient(135deg, var(--bg-3), var(--bg-4));
                  border: 1px solid var(--border); border-radius: 16px; padding: 24px;
                  box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
    .upload-zone { border: 2px dashed var(--border); border-radius: 12px; padding: 36px;
                    text-align: center; cursor: pointer; transition: border-color 0.2s, background 0.2s; }
    .upload-zone:hover, .upload-zone.dragging { border-color: var(--accent); background: rgba(0,212,163,0.04); }
    .upload-zone .icon { font-size: 48px; opacity: 0.7; margin-bottom: 8px; }
    .btn-coord { padding: 12px 24px; border-radius: 12px; border: none; font-weight: 600;
                  cursor: pointer; background: linear-gradient(135deg, var(--accent), #00a37e);
                  color: #000; margin-top: 16px; box-shadow: 0 4px 12px rgba(0,212,163,0.3);
                  transition: transform 0.1s, box-shadow 0.2s; }
    .btn-coord:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(0,212,163,0.4); }
    .btn-coord:disabled { opacity: 0.5; cursor: not-allowed; }
    .result-card { background: linear-gradient(135deg, var(--bg-3), var(--bg-4));
                    border: 1px solid var(--border); border-radius: 14px; padding: 24px; margin-top: 24px; }
    .result-header { display: flex; flex-direction: column; gap: 6px; margin-bottom: 18px; }
    .class-badge { display: inline-block; align-self: flex-start;
                   padding: 8px 18px; border-radius: 999px;
                   background: linear-gradient(135deg, rgba(0,212,163,0.25), rgba(0,212,163,0.1));
                   color: var(--accent); font-weight: 800; font-size: 18px; }
    .class-desc { color: var(--text-muted); font-size: 13px; line-height: 1.5; }
    .confidence-block { margin-bottom: 16px; }
    .conf-row { display: flex; justify-content: space-between; font-size: 13px;
                color: var(--text-muted); margin-bottom: 6px; }
    .conf-pct { color: var(--text); font-weight: 700; }
    .conf-bar-wrap { height: 10px; background: var(--bg-1); border-radius: 999px; overflow: hidden; }
    .conf-bar { height: 100%; border-radius: 999px; transition: width 0.4s ease; }
    .warn-banner { background: rgba(234,88,12,0.08); border: 1px solid rgba(234,88,12,0.3);
                   border-radius: 10px; padding: 12px 14px; margin: 16px 0;
                   font-size: 13px; line-height: 1.5; }
    .warn-banner strong { color: #fb923c; }
    .warn-tip { color: var(--text-muted); margin-top: 6px; font-size: 12.5px; }
    .section-title { font-size: 14px; margin: 18px 0 10px;
                      color: var(--text); font-weight: 600; }
    .prob-list { display: flex; flex-direction: column; gap: 8px; }
    .prob-item { font-size: 13px; }
    .prob-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
    .prob-name { color: var(--text); }
    .prob-pct { color: var(--text-muted); }
    .prob-bar-wrap { height: 8px; background: var(--bg-1); border-radius: 999px; overflow: hidden; }
    .prob-bar { height: 100%; transition: width 0.4s ease; }
    .angle-block { padding: 10px 0; border-bottom: 1px dashed var(--border); font-size: 13px; }
    .angle-block:last-of-type { border-bottom: none; }
    .angle-head { display: flex; justify-content: space-between; margin-bottom: 6px; }
    .angle-label { color: var(--text); font-weight: 600; }
    .angle-vals { color: var(--text-muted); font-size: 12.5px; }
    .angle-track { position: relative; height: 18px; background: var(--bg-1);
                    border-radius: 6px; margin: 6px 0; }
    .angle-ref { position: absolute; top: 0; height: 100%;
                  background: rgba(0,212,163,0.25); border-radius: 6px; }
    .angle-user { position: absolute; top: -4px; width: 4px; height: 26px;
                   background: #fb923c; border-radius: 2px;
                   box-shadow: 0 0 0 2px rgba(0,0,0,0.6); transform: translateX(-2px); }
    .angle-axis { position: absolute; bottom: -16px; left: 0; right: 0;
                   display: flex; justify-content: space-between;
                   font-size: 10px; color: var(--text-muted); }
    .angle-foot { font-size: 11.5px; margin-top: 18px; color: var(--text-muted); }
    .angle-ok { color: var(--accent); font-weight: 600; }
    .angle-warn { color: #fb923c; font-weight: 600; }
    .feedback-box { background: rgba(0,212,163,0.05); border-left: 3px solid var(--accent);
                    padding: 14px 16px; border-radius: 8px; font-size: 14px; line-height: 1.7;
                    white-space: pre-wrap; }
    .timing-details { margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--border);
                       color: var(--text-muted); font-size: 12px; }
    .timing-details summary { cursor: pointer; padding: 4px 0; }
    .timing-row { padding: 3px 0 3px 14px; }
    /* 업로드 가이드 */
    .upload-guide { background: rgba(0,212,163,0.05); border-left: 3px solid var(--accent);
                    border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;
                    font-size: 12.5px; line-height: 1.55; color: var(--text-muted); }
    .upload-guide strong { color: var(--text); }
    .loading-spinner { display: inline-block; width: 14px; height: 14px;
                        border: 2px solid rgba(0,0,0,0.2); border-top-color: #000;
                        border-radius: 50%; animation: spin 0.6s linear infinite;
                        margin-right: 8px; vertical-align: middle; }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="menu" value="pose"/>
</jsp:include>

<section class="pose-hero">
  <h1><span class="hero-emoji">🏃</span>AI 자세 분석</h1>
  <p>풋살 킥 영상을 업로드하면 AI가 자세를 분석해 드려요.<br>
    MediaPipe로 33개 관절을 추출하고, 학습된 모델이 인사이드킥·인스텝킥·인프런트킥 중 어느 자세인지 분류 + 자연어 피드백을 제공합니다.
    <small style="color:var(--text-muted)">(드리블·패스 분류는 Phase 2 예정)</small></p>
</section>

<main class="pose-wrap">
  <div class="pose-card">
    <div class="upload-guide">
      <strong>📌 더 정확한 분석을 위한 촬영 가이드</strong><br>
      · <strong>정면 카메라</strong>에서 임팩트 순간이 포함된 <strong>5~10초</strong> 영상<br>
      · 사람이 화면 중앙에 전신으로 보이도록<br>
      · 정지 자세 / 측면 클로즈업 / 사람 다수 / 역광은 피해주세요
    </div>
    <div id="uploadZone" class="upload-zone">
      <div class="icon">📹</div>
      <p style="margin:0">여기에 mp4 영상을 드롭하거나 클릭해서 선택하세요<br>
        <small style="color:var(--text-muted)">최대 50MB · 30초 이내 권장</small></p>
      <input type="file" id="fileInput" accept="video/mp4,video/quicktime" style="display:none">
    </div>
    <div id="fileName" style="margin-top:12px; color:var(--text-muted); font-size:14px"></div>
    <button id="analyzeBtn" class="btn-coord" disabled>✨ 자세 분석 시작</button>
  </div>

  <div id="resultArea" style="display:none"></div>
</main>

<script>window.POSE_CTX = '${pageContext.request.contextPath}';</script>
<script src="${pageContext.request.contextPath}/resources/script/pose_analyzer.js"></script>
</body>
</html>
