# letsfutsal AI 기능 확장 로드맵

> 포트폴리오·이력서·면접 활용 목적으로 설계된 AI 기능 3종 추가 계획  
> 작성일: 2026-05-19

---

## 구현 순서

**2 → 3 → 1** 순으로 진행 (RAG → 에이전트 → ML)

각 기능은 독립 사이클로 진행:  
`브레인스토밍 → spec.md → writing-plans → 구현`

---

## 기능 1. 풋살 킥·드리블 자세 분석기 (ML / 이미지)

**핵심 기술**: MediaPipe Pose + 커스텀 분류 모델

### 기능 설명
- 사용자가 킥/드리블 영상 또는 웹캠 스트림 업로드
- MediaPipe로 33개 관절 좌표(스켈레톤) 추출
- 관절 각도(무릎 각도, 발 스윙 궤적, 체중 이동) 계산
- 올바른 자세 vs 잘못된 자세 분류 모델 (scikit-learn 또는 TensorFlow Lite)
- "무릎이 너무 잠겨 있습니다", "발목 각도 개선 필요" 등 피드백 반환

### 데이터
- AI Hub (https://aihub.or.kr) — 축구/풋살 동작 포함, 관절 어노테이션 제공

### 기술 스택
- Python, MediaPipe, OpenCV, scikit-learn / TensorFlow Lite
- FastAPI, WebSocket

### 난이도 / 기간
- 높음 / 1~2주 (데이터 수집·모델 학습 포함)

### 이력서 포인트
> MediaPipe 기반 풋살 동작 포즈 추정 모델 구현 (AI Hub 스포츠 데이터 활용)

---

## 기능 2. RAG 기반 풋살 지식 챗봇 (LLM 업그레이드) ✅ 구현 완료 (2026-05-19)

**핵심 기술**: LangChain + ChromaDB + Claude API + Intent Router (하이브리드)

### 구현 결과
- **하이브리드 라우터**: 키워드 사전 1차 → 미스 시 Claude Tool Use 분류기 폴백 → KNOWLEDGE/ADVICE 분기
- **RAG 파이프라인**: `jhgan/ko-sroberta-multitask` 한국어 임베딩 + ChromaDB persist + 시스템 프롬프트 컨텍스트 주입
- **Citation 자동 첨부**: top-4 청크의 `source`/`section`/`page`/`score` JSON 반환 → JSP 위젯에서 `📚` 표시
- **우아한 폴백**: Python ai-service 다운 / RAG 실패 시 기존 Claude 직접 호출 경로로 자동 폴백
- **정량 평가**: 골든셋 20문항(KNOWLEDGE 18 + ADVICE 분류 검증 2) + 5개 지표 자동 측정 스크립트

### 산출물
- Python: `ai-service/rag/` 6개 모듈, `eval/run_eval.py`, `data/raw/` 18개 코퍼스 (FIFA 풋살 규칙 13조 + 전술/훈련 5종, 38청크)
- Java: `IntentRouter`, `RagClient`, `AiService` 라우팅 진입점, `ChatResponseDTO`/`CitationDTO`
- 단위 테스트 45개 (Python 36 + Java 9) 통과
- 관련 문서: [spec](superpowers/specs/2026-05-19-rag-chatbot-design.md), [plan](superpowers/plans/2026-05-19-rag-chatbot.md), [ai-service/README.md](../ai-service/README.md)

### 기술 스택
- LangChain (text splitter), ChromaDB (persistent), sentence-transformers
- Claude API (claude-sonnet-4-6) — RAG 답변 + Tool Use 분류
- Python FastAPI + python-dotenv
- Spring MVC + RestTemplate (Java 호출 경로)

### 난이도 / 기간
- 보통 / 2.5일 (브레인스토밍·spec·plan 포함)

### 이력서 포인트
> LangChain + ChromaDB 기반 한국어 RAG 챗봇 설계·구현. 키워드 사전과 Claude Tool Use 분류기를 결합한 하이브리드 Intent Router로 KNOWLEDGE/ADVICE 경로를 동적 분기. Citation 자동 첨부로 hallucination 방지, 골든셋 20문항 기반 retrieval@k·answer faithfulness 정량 평가.

---

## 기능 3. LangGraph 매치 코디네이터 + 토너먼트 에이전트 ✅ 구현 완료 (2026-05-19)

**핵심 기술**: LangGraph + Multi-Agent + Tool Use

### 구현 결과
- **하이브리드 그래프**: `parse_intent` 노드(Claude Tool Use)가 SINGLE/TOURNAMENT 분류 → conditional edge로 분기
- **단일 매치**: `single_stadium → single_team → single_match → single_review` 순차 노드
- **토너먼트**: StadiumAgent + TeamAgent를 `ThreadPoolExecutor`로 병렬 실행 → MatchAgent로 대진표·매치 통합
- **하이브리드 DB 반영**: 검색은 자동, INSERT는 미리보기 → 사용자 확정 → 트랜잭션
- **별도 페이지** `/ai/coordinator`: 자연어 입력 + 미리보기 카드 편집 + 확정 버튼
- **정량 평가**: 시나리오 8개 + 4개 지표(intent_acc, tool_correctness, proposal_validity, e2e_success)

### 산출물
- Python: `ai-service/agent/` 6개 모듈 (`state`, `schemas`, `springboot_client`, `tools`, `nodes`, `subagents`, `graph`), `eval/run_agent_eval.py`
- Java: `AgentController`, `AgentService`, `AgentDataController`, DTO 5종(`AgentRequest`, `Proposal`, `MatchProposal`, `Bracket`, `ConfirmRequest`)
- JSP: `/ai/coordinator` 페이지 + `agent_coordinator.js` 편집 UI
- 단위 테스트 ~40개(Python 36 + Java 6) 통과
- 관련: [spec](superpowers/specs/2026-05-19-langgraph-agent-design.md), [plan](superpowers/plans/2026-05-19-langgraph-agent.md)

### 기능 설명
**기본 (매치 코디네이터)**  
"이번 주말 서울 강남에서 팀 경기 잡아줘" 입력 시:

```
[사용자 의도 파악]
    → [경기장 검색 Tool]
    → [팀 멤버 가용성 확인 Tool]
    → [매치 추천 Tool]
    → [최적 경기 생성]
    → [결과 요약 반환]
```

각 단계가 LangGraph StateGraph 노드로 구성.

**확장 (토너먼트 기획 - 멀티에이전트)**  
병렬 Sub-agent 패턴:
- `StadiumAgent`: 경기장 가용성 조회
- `TeamAgent`: 팀원 스케줄/실력 분석
- `MatchAgent`: 매치 생성·조율

LangGraph 병렬 노드로 Stadium + Team 동시 검색 후 Match 생성.

### 기술 스택
- LangGraph, LangChain
- Claude API (Tool Use 기능)
- Python FastAPI (기존 recommend_service 확장)

### 난이도 / 기간
- 보통~높음 / 3~5일 (LangGraph 학습 포함)

### 이력서 포인트
> LangGraph StateGraph 기반 멀티에이전트 시스템 설계 (Tool Use, 병렬 오케스트레이션)

---

## 에이전트 옵션 전체 비교 (취업·포트폴리오 관점)

| 순위 | 이름 | 핵심 기술 포인트 | 난이도 | 추천 이유 |
|:---:|---|---|:---:|---|
| **1위** | **C. 토너먼트 기획** | 병렬 멀티에이전트 오케스트레이션, LangGraph 분기·병렬 노드 | 높음 | 멀티에이전트 구조 가장 명확, 면접 설명 용이 |
| **2위** | **기존. 매치 코디네이터** | LangGraph StateGraph 기본 패턴, Tool Use | 보통 | LangGraph 기본기 완성도 높음, 구현 현실성 최고 |
| **3위** | D. 전술 분석 | 도메인 특화 추론, 데이터 기반 LLM 활용 | 보통 | 풋살 도메인 깊이, 시연 임팩트 강함 |
| **4위** | A. 팀 스카우트 | Retry 루프, 조건 완화 재검색 패턴 | 보통 | 실용적, ReAct 패턴 설명 가능 |
| **5위** | B. 성과 리포트 | 데이터 수집→분석→생성 파이프라인 | 낮음 | 빠른 구현, 에이전트 특성 약함 |

**전략**: 기존(매치 코디네이터) 먼저 → C(토너먼트)로 자연스럽게 확장

---

## 기술 커버리지 (7개 전부 커버)

| 기술 | 기능 1 (ML) | 기능 2 (RAG) | 기능 3 (Agent) |
|---|:---:|:---:|:---:|
| LLM API 연동 | | ✅ | ✅ |
| AI Agent | | | ✅ |
| LangChain | | ✅ | ✅ |
| LangGraph | | | ✅ |
| 멀티 에이전트 | | | ✅ |
| RAG | | ✅ | |
| ML / 컴퓨터 비전 | ✅ | | |

---

## 이력서 활용 문구

```
- MediaPipe 기반 풋살 동작 포즈 추정 모델 구현 (AI Hub 스포츠 데이터 활용)
- LangChain + ChromaDB RAG 파이프라인 설계, Claude API 연동 지식 챗봇 고도화
- LangGraph StateGraph 기반 멀티에이전트 시스템 설계 (Tool Use, 병렬 오케스트레이션)
```

---

## 다음 단계

1. ~~**브레인스토밍 #1**: 기능 2 (RAG 챗봇)~~ ✅ 2026-05-19 구현 완료
2. ~~**브레인스토밍 #2**: 기능 3 (LangGraph 에이전트)~~ ✅ 2026-05-19 구현 완료
3. **브레인스토밍 #3**: 기능 1 (ML 포즈 분석)
