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

## 기능 2. RAG 기반 풋살 지식 챗봇 (LLM 업그레이드)

**핵심 기술**: LangChain + ChromaDB + Claude API

### 기능 설명
기존 챗봇(단순 프롬프트)을 RAG 파이프라인으로 업그레이드:

1. 풋살 규칙서(FIFA Futsal Rules), 전술 문서, 훈련 가이드 PDF
   → 청크 분할 → 벡터 임베딩 → ChromaDB 저장
2. 사용자 질문 → 벡터 유사도 검색으로 관련 문서 3~5개 추출
3. 추출된 문서를 컨텍스트로 Claude API에 전달
4. "오프사이드 규칙이 뭐야?", "4-0 포메이션 전술은?" 같은 질문에 문서 기반 정확한 답변

### 기술 스택
- LangChain, ChromaDB (or FAISS), sentence-transformers
- Claude API (claude-sonnet-4-6)
- Python FastAPI (기존 ai_service 확장)

### 난이도 / 기간
- 낮음~보통 / 1~2일 (기존 챗봇 인프라 재활용)

### 이력서 포인트
> LangChain + ChromaDB RAG 파이프라인 설계, Claude API 연동 지식 챗봇 고도화

---

## 기능 3. LangGraph 매치 코디네이터 + 토너먼트 에이전트

**핵심 기술**: LangGraph + Multi-Agent + Tool Use

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

1. **브레인스토밍 #1**: 기능 2 (RAG 챗봇) — `docs/superpowers/specs/` 에 spec.md 생성
2. **브레인스토밍 #2**: 기능 3 (LangGraph 에이전트)
3. **브레인스토밍 #3**: 기능 1 (ML 포즈 분석)
