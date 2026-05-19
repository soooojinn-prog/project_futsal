# RAG 풋살 챗봇 평가 리포트

- 실행 시각: 2026-05-19 20:23
- KNOWLEDGE 문항 수: 18
- ADVICE 문항 수: 2

## 핵심 지표

| 지표 | 값 | 목표 | 통과 |
|---|---|---|---|
| retrieval@1 | 0.722 | ≥ 0.70 | ✅ |
| retrieval@4 | 1.000 | ≥ 0.90 | ✅ |
| citation_present | 1.000 | ≥ 0.95 | ✅ |
| answer_faithfulness | 0.556 | ≥ 0.80 | ❌ |
| advice_classification_acc | 1.000 | ≥ 0.90 | ✅ |

## 문항별 결과 (KNOWLEDGE)

| id | query | expected | top-1 | top-k | faithful |
|---|---|---|---|---|---|
| q01 | 풋살에 오프사이드 규칙이 있어? | rules 11 offside | ✅ | ✅ | ✅ |
| q02 | 풋살 경기 시간은 몇 분이야? | rules 07 duration | ✅ | ✅ | ✅ |
| q03 | 풋살에서 누적 파울이 5개를 넘으면 어떻게 돼? | rules 12 fouls | ✅ | ✅ | ✅ |
| q04 | 4-0 포메이션이 뭐야? | formations 4 0 | ✅ | ✅ | ❌ |
| q05 | 3-1 포메이션의 특징은? | formations 3 1 | ✅ | ✅ | ✅ |
| q06 | 2-2 포메이션 어떨 때 써? | formations 2 2 | ✅ | ✅ | ✅ |
| q07 | 코너킥은 몇 초 안에 차야 해? | rules 17 corner | ✅ | ✅ | ❌ |
| q08 | 킥인 규칙 알려줘 | rules 15 kickin | ✅ | ✅ | ❌ |
| q09 | 풋살에서 압박 전술이란? | tactics pressing | ✅ | ✅ | ✅ |
| q10 | 카운터 공격은 어떻게 만들어? | tactics pressing | ❌ | ✅ | ✅ |
| q11 | 드리블 기본 훈련법은? | training basics | ✅ | ✅ | ❌ |
| q12 | 패스 연습 어떻게 해? | training basics | ✅ | ✅ | ❌ |
| q13 | 슈팅 기본 자세는? | training basics | ✅ | ✅ | ❌ |
| q14 | 풋살 골키퍼는 볼을 몇 초 잡고 있을 수 있어? | rules 16 goalclearance | ❌ | ✅ | ✅ |
| q15 | 풋살 페널티킥 거리는 얼마야? | rules 14 penalty | ❌ | ✅ | ✅ |
| q16 | 피보 포지션이 뭐야? | formations 4 0 | ❌ | ✅ | ❌ |
| q17 | 알라 포지션 설명 | formations 3 1 | ✅ | ✅ | ❌ |
| q18 | 풋살은 한 팀에 몇 명이야? | rules 03 players | ❌ | ✅ | ✅ |

## 라우터 분류 결과 (ADVICE)

| id | query | classified_as | ok |
|---|---|---|---|
| q19 | 우리 팀이 자꾸 지는데 어떡하지? | ADVICE | ✅ |
| q20 | 오늘 풋살하기 좋은 날씨인가? | ADVICE | ✅ |
