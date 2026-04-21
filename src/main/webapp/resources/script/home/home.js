document.addEventListener('DOMContentLoaded', () => {
  const dateContainer = document.getElementById('dateFilters');
  const matchList = document.getElementById('matchList');

  const today = new Date();
  for (let i = 0; i < 8; i++) {
    const d = new Date();
    d.setDate(today.getDate() + i);
    const offset = d.getTimezoneOffset() * 60000;
    const localISOTime = (new Date(d - offset)).toISOString().split('T')[0];

    const weekDays = ['일', '월', '화', '수', '목', '금', '토'];
    const dayOfWeek = weekDays[d.getDay()];
    const displayStr = `${d.getMonth() + 1}/${d.getDate()} (${dayOfWeek})`;

    const btn = document.createElement('div');
    btn.innerHTML = `
      <input type="radio" class="btn-check" name="matchDate" id="date${i}" value="${localISOTime}" ${i === 0 ? 'checked' : ''}>
      <label class="btn btn-outline-secondary text-nowrap" for="date${i}">${displayStr}</label>
    `;
    dateContainer.appendChild(btn.firstElementChild);
    dateContainer.appendChild(btn.lastElementChild);
  }

  const matchTypeMap = {
    'INDIVIDUAL': '개인',
    'RENT': '대여',
    'TEAM': '팀',
  };

  const matchTypeMapReverse = {
    '개인': 'INDIVIDUAL',
    '대여': 'RENT',
    '팀': 'TEAM',
  };

  const matchGenderMap = {
    'BOTH': '혼성',
    'FEMALE': '여성',
    'MALE': '남성',
  };

  const matchGradeMap = {
    0: '입문',
    1: '초보',
    2: '중수',
    3: '고수',
  };

  function getCardTypeClass(matchType) {
    switch (matchType) {
      case 'INDIVIDUAL': return 'type-individual';
      case 'TEAM':       return 'type-team';
      case 'RENT':       return 'type-rent';
      default:           return 'type-individual';
    }
  }

  function getBadgeClass(matchType) {
    switch (matchType) {
      case 'INDIVIDUAL': return 'badge-individual';
      case 'TEAM':       return 'badge-team';
      case 'RENT':       return 'badge-rent';
      default:           return 'badge-individual';
    }
  }

  function fetchMatches() {
    const date = document.querySelector('input[name="matchDate"]:checked').value;
    const region = document.getElementById('regionFilter').value;
    const typeUI = document.querySelector('input[name="matchType"]:checked').value;
    const type = matchTypeMapReverse[typeUI] || typeUI;

    matchList.innerHTML = `
      <div class="col-12 text-center py-5">
        <div class="spinner-border text-primary" role="status"></div>
        <p class="mt-3 text-muted">매치를 불러오는 중입니다...</p>
      </div>
    `;

    fetch(`${contextPath}/api/matches?date=${date}&region=${region}&type=${type}`)
      .then(res => res.json())
      .then(data => renderMatches(data))
      .catch(() => {
        matchList.innerHTML = `
          <div class="col-12">
            <div class="match-card text-center py-4">
              <p class="text-muted mb-0">데이터를 불러오는데 실패했습니다.</p>
            </div>
          </div>
        `;
      });
  }

  function renderMatches(matches) {
    if (matches.length === 0) {
      matchList.innerHTML = `
        <div class="col-12">
          <div class="match-card text-center py-4">
            <p class="text-muted mb-0">해당 조건에 맞는 매치가 없습니다.</p>
          </div>
        </div>
      `;
      return;
    }

    matchList.innerHTML = matches.map((match, idx) => {
      const typeLabel = matchTypeMap[match.matchType] || match.matchType;
      const displayTime = match.startHour ? match.startHour.substring(0, 5) : '00:00';
      const gender = matchGenderMap[match.gender] || match.gender;
      const minGrade = matchGradeMap[match.minGrade] ?? match.minGrade;
      const maxGrade = matchGradeMap[match.maxGrade] ?? match.maxGrade;
      const badgeClass = getBadgeClass(match.matchType);
      const typeClass = getCardTypeClass(match.matchType);
      const delayClass = `delay-${Math.min(idx, 7)}`;

      return `
        <div class="col-12 col-md-6 col-lg-4">
          <div class="match-card ${typeClass} ${delayClass}">
            <div class="d-flex justify-content-between align-items-start">
              <span class="badge ${badgeClass}">${typeLabel}</span>
              <span class="match-time">${displayTime}</span>
            </div>
            <h5 class="match-stadium">${match.stadiumName || '경기장 명칭'}</h5>
            <p class="match-info">${match.region} · ${gender} · ${minGrade}~${maxGrade}</p>
            <div class="d-flex justify-content-between align-items-center mt-auto">
              <span class="match-status"><span class="count">${match.status}</span>명 참여중</span>
              <a href="${contextPath}/match/${match.matchId}" class="btn-detail">상세보기</a>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  document.getElementById('dateFilters').addEventListener('change', fetchMatches);
  document.getElementById('regionFilter').addEventListener('change', fetchMatches);
  document.getElementsByName('matchType').forEach(el => el.addEventListener('change', fetchMatches));

  fetchMatches();
});
