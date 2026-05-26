(function () {
  const ctx = window.POSE_CTX || '';
  const fileInput = document.getElementById('fileInput');
  const uploadZone = document.getElementById('uploadZone');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const fileNameEl = document.getElementById('fileName');
  const resultArea = document.getElementById('resultArea');
  let selectedFile = null;

  // 클래스별 기준 각도 (학습 데이터 기반 + Claude 프롬프트 동기화)
  const REF = {
    INSIDE_KICK: {
      label: '인사이드킥',
      desc: '발 안쪽으로 부드럽게 차는 패스용 자세. 디딤발 살짝 굽힘 + 차는 발 외전.',
      knee: [150, 165], // 디딤발 무릎
      ankle: [85, 100], // 차는 발 발목
    },
    INSTEP_KICK: {
      label: '인스텝킥',
      desc: '발등 중앙으로 강하게 차는 슈팅용 자세. 디딤발 확실한 굽힘 + 발등 면 임팩트.',
      knee: [135, 155],
      ankle: [120, 135],
    },
  };

  // ───────── 업로드 핸들러 (기존 유지) ─────────
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

  // ───────── 시각적 결과 렌더 ─────────
  function renderResult(d) {
    const refInfo = REF[d.pose_class] || { label: d.class_name, desc: '', knee: [0, 180], ankle: [0, 180] };
    const conf = d.confidence || 0;
    const confPct = (conf * 100).toFixed(1);

    // 신뢰도 색상 + 라벨
    let confColor, confLabel, warningBanner = '';
    if (conf >= 0.85) {
      confColor = 'linear-gradient(90deg, #16a34a, #22c55e)';
      confLabel = '확신도 높음';
    } else if (conf >= 0.70) {
      confColor = 'linear-gradient(90deg, #eab308, #facc15)';
      confLabel = '확신도 보통';
    } else {
      confColor = 'linear-gradient(90deg, #ea580c, #fb923c)';
      confLabel = '확신도 낮음';
    }

    // 75% 미만이면 경고 배너
    if (conf < 0.75) {
      warningBanner =
        '<div class="warn-banner">' +
        '<strong>⚠ 분석 정확도가 ' + (conf >= 0.65 ? '보통' : '낮습니다') + '</strong>' +
        '<div class="warn-tip">아래 가이드대로 다시 촬영하면 더 정확합니다:<br>' +
        '· <b>정면 카메라</b>에서 임팩트 순간 포함 <b>5~10초</b> 영상<br>' +
        '· 사람이 화면 가운데, 전신이 보이도록<br>' +
        '· 정지·측면·다수 인물·역광은 피해주세요' +
        '</div></div>';
    }

    const ka = d.key_angles;
    const tm = d.timing_ms;

    // 클래스 확률 막대
    const probs = d.class_probabilities || {};
    const probBar = renderProbBar(probs);

    // 각도 비교 막대 (좌/우 무릎·발목 4개)
    const anglesBlock =
      angleCompareRow('좌 무릎', ka.left_knee, refInfo.knee, '디딤발/차는 발 중 하나의 무릎') +
      angleCompareRow('우 무릎', ka.right_knee, refInfo.knee, '디딤발/차는 발 중 하나의 무릎') +
      angleCompareRow('좌 발목', ka.left_ankle, refInfo.ankle, '발 임팩트 면') +
      angleCompareRow('우 발목', ka.right_ankle, refInfo.ankle, '발 임팩트 면');

    resultArea.style.display = 'block';
    resultArea.innerHTML =
      '<div class="result-card">' +
      // 헤더
      '<div class="result-header">' +
      '<div class="class-badge">' + escapeHtml(refInfo.label) + '</div>' +
      '<div class="class-desc">' + escapeHtml(refInfo.desc) + '</div>' +
      '</div>' +
      // 신뢰도 게이지
      '<div class="confidence-block">' +
      '<div class="conf-row"><span>신뢰도</span><span class="conf-pct">' + confPct + '% · ' + confLabel + '</span></div>' +
      '<div class="conf-bar-wrap"><div class="conf-bar" style="width:' + confPct + '%;background:' + confColor + '"></div></div>' +
      '</div>' +
      // 경고 배너
      warningBanner +
      // 클래스 확률
      '<h3 class="section-title">📊 분류 확률</h3>' +
      probBar +
      // 각도 비교
      '<h3 class="section-title">🦵 핵심 관절 각도 (' + escapeHtml(refInfo.label) + ' 기준과 비교)</h3>' +
      anglesBlock +
      // Claude 피드백
      '<h3 class="section-title">💬 코치 피드백</h3>' +
      '<div class="feedback-box">' + escapeHtml(d.feedback) + '</div>' +
      // 타이밍 (접힘)
      '<details class="timing-details">' +
      '<summary>⏱ 처리 시간 상세 (' + tm.total + 'ms)</summary>' +
      '<div class="timing-row">프레임 추출: ' + tm.frame_extract + ' ms</div>' +
      '<div class="timing-row">MediaPipe 키포인트: ' + tm.mediapipe + ' ms</div>' +
      '<div class="timing-row">자세 분류: ' + tm.classify + ' ms</div>' +
      '<div class="timing-row">Claude 피드백 생성: ' + tm.feedback + ' ms</div>' +
      '</details>' +
      '</div>';
  }

  function renderProbBar(probs) {
    const entries = Object.entries(probs);
    if (!entries.length) return '';
    entries.sort((a, b) => b[1] - a[1]);
    const total = entries.reduce((s, [, v]) => s + v, 0) || 1;
    let html = '<div class="prob-list">';
    const colors = ['#22c55e', '#3b82f6', '#a855f7'];
    entries.forEach(([cls, p], i) => {
      const pct = ((p / total) * 100).toFixed(1);
      const label = (REF[cls] && REF[cls].label) || cls;
      html +=
        '<div class="prob-item">' +
        '<div class="prob-row"><span class="prob-name">' + escapeHtml(label) + '</span><span class="prob-pct">' + pct + '%</span></div>' +
        '<div class="prob-bar-wrap"><div class="prob-bar" style="width:' + pct + '%;background:' + colors[i % colors.length] + '"></div></div>' +
        '</div>';
    });
    html += '</div>';
    return html;
  }

  function angleCompareRow(label, stats, ref, hint) {
    const v = stats.mean;
    const inRange = v >= ref[0] && v <= ref[1];
    const status = inRange
      ? '<span class="angle-ok">✅ 기준 범위 안</span>'
      : '<span class="angle-warn">⚠ 기준 범위 밖 (' + (v < ref[0] ? '부족' : '과다') + ')</span>';
    // 축: 0~180°를 가정. 기준 범위와 사용자 값을 막대 위에 표시
    const refLeft = (ref[0] / 180) * 100;
    const refWidth = ((ref[1] - ref[0]) / 180) * 100;
    const userLeft = Math.max(0, Math.min(100, (v / 180) * 100));
    return (
      '<div class="angle-block">' +
      '<div class="angle-head">' +
      '<span class="angle-label">' + escapeHtml(label) + '</span>' +
      '<span class="angle-vals">평균 <b>' + v.toFixed(1) + '°</b> ' +
      '<small>(min ' + stats.min.toFixed(0) + ' / max ' + stats.max.toFixed(0) + ')</small></span>' +
      '</div>' +
      '<div class="angle-track">' +
      '<div class="angle-ref" style="left:' + refLeft + '%;width:' + refWidth + '%"></div>' +
      '<div class="angle-user" style="left:' + userLeft + '%"></div>' +
      '<div class="angle-axis"><span>0°</span><span>90°</span><span>180°</span></div>' +
      '</div>' +
      '<div class="angle-foot">' + status +
      ' · 기준 ' + ref[0] + '~' + ref[1] + '° · <small>' + escapeHtml(hint) + '</small></div>' +
      '</div>'
    );
  }

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
})();
