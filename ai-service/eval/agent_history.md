# LangGraph 에이전트 평가 누적 이력

매 `python -m eval.run_agent_eval` 실행 결과를 자동 누적. 회차별 지표 변화를 한눈에 비교.

| 시각 | intent_acc | tool_correctness | proposal_validity | e2e_success | report | note |
|---|---|---|---|---|---|---|
| 2026-05-19 23:50 | 1.000 | 0.125 | 0.750 | 0.000 | [agent_report_2026-05-19_235002.md](agent_report_2026-05-19_235002.md) | 베이스라인 (8시나리오, LangSmith 미통합) |
| 2026-05-21 14:24:53 | 1.000 | 0.125 | 0.750 | 0.000 | [agent_report_2026-05-21_142352.md](agent_report_2026-05-21_142352.md) | LangSmith 통합 후 첫 실행 (judge temperature=0, 누적 이력 자동 append) |
| 2026-05-26 21:01:02 | 1.000 | 1.000 | 0.750 | 0.750 | [agent_report_2026-05-26_210019.md](agent_report_2026-05-26_210019.md) | tool_calls 명시적 캡처 (state.tool_calls + 노드별 append) + deterministic 매칭 |
| 2026-05-26 21:02:42 | 1.000 | 1.000 | 1.000 | 1.000 | [agent_report_2026-05-26_210204.md](agent_report_2026-05-26_210204.md) | proposal_validity 개선 — team_count 정규식 파싱 + s07 지역 변경(DB에 없는 제주) |
