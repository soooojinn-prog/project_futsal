(function () {
  const ctx = window.AGENT_CTX || '';
  let currentProposal = null;

  document.getElementById('runBtn').addEventListener('click', async function () {
    const text = document.getElementById('userInput').value.trim();
    if (!text) return;

    this.disabled = true;
    this.textContent = '에이전트 실행 중...';

    try {
      const resp = await fetch(ctx + '/ai/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userInput: text })
      });
      const data = await resp.json();
      if (!resp.ok) {
        alert(data.error || '오류가 발생했습니다.');
        return;
      }
      currentProposal = data;
      renderProposal(data);
    } catch (e) {
      alert('연결 오류: ' + e.message);
    } finally {
      this.disabled = false;
      this.textContent = '에이전트 실행';
    }
  });

  document.getElementById('confirmBtn').addEventListener('click', async function () {
    if (!currentProposal) return;
    this.disabled = true;
    this.textContent = '저장 중...';

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
        alert(data.error || '저장 실패');
        return;
      }
      document.getElementById('resultArea').style.display = 'block';
      document.getElementById('resultArea').textContent =
        '✅ 매치 ' + data.createdMatchIds.length + '건 생성 완료. IDs: ' + data.createdMatchIds.join(', ');
      document.getElementById('proposalArea').style.display = 'none';
    } catch (e) {
      alert('저장 오류: ' + e.message);
    } finally {
      this.disabled = false;
      this.textContent = '✅ 매치 확정 (DB 저장)';
    }
  });

  function renderProposal(p) {
    document.getElementById('proposalArea').style.display = 'block';

    const warnBox = document.getElementById('warningsBox');
    if (p.warnings && p.warnings.length) {
      warnBox.style.display = 'block';
      warnBox.innerHTML = '<strong>⚠️ 경고:</strong><br>' +
        p.warnings.map(w => '• ' + escapeHtml(w)).join('<br>');
    } else {
      warnBox.style.display = 'none';
    }

    const list = document.getElementById('matchList');
    list.innerHTML = '';
    (p.matches || []).forEach(function (m, idx) {
      const card = document.createElement('div');
      card.className = 'match-card';
      const stageHtml = m.stage
        ? '<span class="stage-badge">' + escapeHtml(m.stage) + '</span> '
        : '';
      const teamB = m.team_b ? ' vs ' + escapeHtml(m.team_b.name) : '';
      card.innerHTML =
        '<div>' + stageHtml +
        '<label>시간</label>' +
        '<input type="datetime-local" value="' + (m.start_time || '').substring(0, 16) +
        '" data-idx="' + idx + '" data-field="start_time"></div>' +
        '<div><label>경기장</label>' + escapeHtml(m.stadium_name) +
        ' (id ' + m.stadium_id + ')</div>' +
        '<div><label>팀</label>' + escapeHtml(m.team_a ? m.team_a.name : '?') + teamB + '</div>' +
        '<div style="margin-top:8px"><button class="coord-btn danger" data-remove="' + idx + '">삭제</button></div>';
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
