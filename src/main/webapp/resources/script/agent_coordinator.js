(function () {
  const ctx = window.AGENT_CTX || '';
  let currentProposal = null;

  const runBtn = document.getElementById('runBtn');
  const confirmBtn = document.getElementById('confirmBtn');
  const userInput = document.getElementById('userInput');

  // 예시 칩 클릭 → 입력창 채우기
  document.querySelectorAll('.example-chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      userInput.value = chip.dataset.example;
      userInput.focus();
    });
  });

  runBtn.addEventListener('click', async function () {
    const text = userInput.value.trim();
    if (!text) {
      userInput.focus();
      return;
    }

    this.disabled = true;
    this.innerHTML = '<span class="loading-spinner"></span>AI가 준비 중이에요...';
    hideResult();

    try {
      const resp = await fetch(ctx + '/ai/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userInput: text })
      });

      if (resp.status === 401) {
        alert('로그인이 필요해요.');
        window.location.href = ctx + '/user/login';
        return;
      }
      if (!resp.ok) {
        const errText = await resp.text();
        let msg = '⚠️ 잠시 후 다시 시도해 주세요.';
        try { msg = JSON.parse(errText).error || msg; } catch (e) {}
        alert(msg);
        return;
      }

      const data = await resp.json();
      currentProposal = data;
      renderProposal(data);
    } catch (e) {
      alert('연결이 원활하지 않아요. 잠시 후 다시 시도해 주세요.');
    } finally {
      this.disabled = false;
      this.innerHTML = '✨ AI에게 맡기기';
    }
  });

  confirmBtn.addEventListener('click', async function () {
    if (!currentProposal) return;
    if (!currentProposal.matches || currentProposal.matches.length === 0) {
      alert('확정할 매치가 없어요. AI에게 다시 요청해 주세요.');
      return;
    }
    this.disabled = true;
    this.innerHTML = '<span class="loading-spinner"></span>매치 만드는 중...';

    try {
      const resp = await fetch(ctx + '/ai/agent/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          proposalId: currentProposal.proposal_id,
          matches: currentProposal.matches
        })
      });
      const data = await resp.json();
      if (!resp.ok) {
        alert(data.error || '저장에 실패했어요. 다시 시도해 주세요.');
        return;
      }
      showResult(data.createdMatchIds || []);
      document.getElementById('proposalArea').style.display = 'none';
    } catch (e) {
      alert('저장 중 오류가 발생했어요: ' + e.message);
    } finally {
      this.disabled = false;
      this.innerHTML = '✅ 이대로 매치 만들기';
    }
  });

  function renderProposal(p) {
    document.getElementById('proposalArea').style.display = 'block';

    const warnBox = document.getElementById('warningsBox');
    const friendlyWarnings = (p.warnings || []).map(prettifyWarning).filter(Boolean);
    if (friendlyWarnings.length) {
      warnBox.style.display = 'block';
      warnBox.innerHTML = '<strong>💡 안내</strong><br>' +
        friendlyWarnings.map(function (w) { return '• ' + escapeHtml(w); }).join('<br>');
    } else {
      warnBox.style.display = 'none';
    }

    const list = document.getElementById('matchList');
    list.innerHTML = '';

    if (!p.matches || p.matches.length === 0) {
      list.innerHTML =
        '<div class="match-card" style="text-align:center;padding:36px 20px;">' +
        '<div style="font-size:42px;opacity:0.4;">🤔</div>' +
        '<div style="color:var(--text-muted);margin-top:8px;">조건에 맞는 매치를 찾지 못했어요. 다른 조건으로 시도해 보세요.</div>' +
        '</div>';
      confirmBtn.style.display = 'none';
      return;
    }
    confirmBtn.style.display = 'block';

    p.matches.forEach(function (m, idx) {
      const card = document.createElement('div');
      card.className = 'match-card';
      const startTime16 = (m.start_time || '').substring(0, 16);
      const stage = m.stage ? '<span class="match-stage">' + escapeHtml(m.stage) + '</span>' : '<span></span>';
      const teamB = m.team_b ? ' vs ' + escapeHtml(m.team_b.name) : '';

      card.innerHTML =
        '<div class="match-header">' +
          stage +
          '<button class="match-remove" data-remove="' + idx + '">🗑️ 삭제</button>' +
        '</div>' +
        '<div class="match-row">' +
          '<span class="label">🕐 시간</span>' +
          '<input type="datetime-local" value="' + startTime16 + '" data-idx="' + idx + '" data-field="start_time">' +
        '</div>' +
        '<div class="match-row">' +
          '<span class="label">🏟️ 경기장</span>' +
          '<span>' + escapeHtml(m.stadium_name || '미정') + '</span>' +
        '</div>' +
        '<div class="match-row">' +
          '<span class="label">👥 팀</span>' +
          '<span>' + escapeHtml((m.team_a && m.team_a.name) || '내 팀') + teamB + '</span>' +
        '</div>';
      list.appendChild(card);
    });

    list.querySelectorAll('input[data-field=start_time]').forEach(function (input) {
      input.addEventListener('change', function () {
        const idx = parseInt(input.dataset.idx, 10);
        currentProposal.matches[idx].start_time = input.value;
      });
    });
    list.querySelectorAll('[data-remove]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const idx = parseInt(btn.dataset.remove, 10);
        currentProposal.matches.splice(idx, 1);
        renderProposal(currentProposal);
      });
    });
  }

  function showResult(ids) {
    const el = document.getElementById('resultArea');
    el.style.display = 'block';
    el.innerHTML =
      '<h3>🎉 매치 생성 완료!</h3>' +
      '<p style="color:var(--text-muted);font-size:14px;">' +
        ids.length + '건의 매치가 등록되었어요. ' +
        '<a href="' + ctx + '/match" style="color:var(--accent);font-weight:600;">매치 목록 보러가기</a>' +
      '</p>';
  }

  function hideResult() {
    document.getElementById('resultArea').style.display = 'none';
  }

  // 사용자 친화 경고 메시지로 변환
  function prettifyWarning(w) {
    if (!w) return null;
    if (w.indexOf('팀 정보가 없어') >= 0) {
      return '팀 일정 충돌은 체크되지 않았어요. 매치 생성 후 직접 확인해 주세요.';
    }
    if (w.indexOf('날짜가 명시되지 않아') >= 0) {
      return w; // 날짜 폴백 알림은 그대로 표시
    }
    if (w.indexOf('경기장이 없습니다') >= 0) {
      return '해당 조건에 맞는 경기장을 찾지 못했어요. 지역을 다시 알려 주세요.';
    }
    if (w.indexOf('시간 충돌') >= 0) {
      return null; // 시간 충돌 노이즈는 숨김
    }
    if (w.indexOf('적합한 매치 슬롯') >= 0) {
      return '해당 시간대에 빈 슬롯이 없어요. 다른 시간을 시도해 보세요.';
    }
    return w;
  }

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
})();
