(function () {
  const ctx = window.POSE_CTX || '';
  const fileInput = document.getElementById('fileInput');
  const uploadZone = document.getElementById('uploadZone');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const fileNameEl = document.getElementById('fileName');
  const resultArea = document.getElementById('resultArea');
  let selectedFile = null;

  uploadZone.addEventListener('click', () => fileInput.click());
  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragging');
  });
  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragging'));
  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragging');
    if (e.dataTransfer.files.length) setFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) setFile(e.target.files[0]);
  });

  function setFile(f) {
    if (!f.type.startsWith('video/')) {
      alert('영상 파일만 업로드 가능해요.');
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      alert('영상은 최대 50MB까지 가능해요.');
      return;
    }
    selectedFile = f;
    fileNameEl.textContent = '✅ 선택됨: ' + f.name + ' (' + (f.size / 1024 / 1024).toFixed(1) + 'MB)';
    analyzeBtn.disabled = false;
  }

  analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<span class="loading-spinner"></span>AI가 분석 중이에요... (5~30초)';
    resultArea.style.display = 'none';

    try {
      const form = new FormData();
      form.append('file', selectedFile);
      const resp = await fetch(ctx + '/ai/pose/analyze', { method: 'POST', body: form });
      if (resp.status === 401) {
        alert('로그인이 필요해요.');
        window.location.href = ctx + '/user/login';
        return;
      }
      const data = await resp.json();
      if (!resp.ok) {
        alert(data.error || data.detail || '분석에 실패했어요.');
        return;
      }
      renderResult(data);
    } catch (e) {
      alert('네트워크 오류: ' + e.message);
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = '✨ 자세 분석 시작';
    }
  });

  function renderResult(d) {
    const ka = d.key_angles;
    const tm = d.timing_ms;
    resultArea.style.display = 'block';
    resultArea.innerHTML =
      '<div class="result-card">' +
      '<div style="margin-bottom:16px"><span class="badge-class">' + escapeHtml(d.class_name) + '</span> ' +
      '<small style="color:var(--text-muted);margin-left:8px">신뢰도 ' + (d.confidence * 100).toFixed(1) + '%</small></div>' +
      '<h3 style="font-size:16px;margin:16px 0 8px">🦵 핵심 관절 각도 (평균)</h3>' +
      angleRow('좌 무릎', ka.left_knee) +
      angleRow('우 무릎', ka.right_knee) +
      angleRow('좌 발목', ka.left_ankle) +
      angleRow('우 발목', ka.right_ankle) +
      '<div class="feedback-box"><strong>💬 코치 피드백</strong><br>' + escapeHtml(d.feedback) + '</div>' +
      '<div class="timing-bar">⏱️ 전체 처리 ' + tm.total + 'ms ' +
      '· 프레임 ' + tm.frame_extract + ' · MediaPipe ' + tm.mediapipe +
      ' · 분류 ' + tm.classify + ' · 피드백 ' + tm.feedback + '</div>' +
      '</div>';
  }

  function angleRow(label, a) {
    return '<div class="angle-row"><span>' + label + '</span>' +
      '<span>평균 <strong>' + a.mean.toFixed(1) + '°</strong> ' +
      '<small style="color:var(--text-muted)">(min ' + a.min.toFixed(0) +
      ' / max ' + a.max.toFixed(0) + ')</small></span></div>';
  }

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
})();
