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
    .angle-row { display: flex; justify-content: space-between; padding: 10px 0;
                  border-bottom: 1px dashed var(--border); font-size: 14px; }
    .angle-row:last-child { border-bottom: none; }
    .badge-class { display: inline-block; padding: 6px 14px; border-radius: 8px;
                    background: rgba(0,212,163,0.15); color: var(--accent); font-weight: 700; }
    .feedback-box { background: rgba(0,212,163,0.05); border-left: 3px solid var(--accent);
                    padding: 16px; border-radius: 6px; margin-top: 16px; line-height: 1.6; }
    .timing-bar { color: var(--text-muted); font-size: 12px; margin-top: 16px;
                   padding-top: 12px; border-top: 1px solid var(--border); }
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
  <h1>🏃 AI 자세 분석</h1>
  <p>풋살 킥/드리블 영상을 업로드하면 AI가 자세를 분석해 드려요.<br>
    MediaPipe로 33개 관절을 추출하고, 학습된 모델이 자세를 4가지로 분류해 자연어 피드백까지 제공합니다.</p>
</section>

<main class="pose-wrap">
  <div class="pose-card">
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
