# AI 통합 설계 문서 — letsfutsal

**날짜**: 2026-04-29  
**목적**: 풋살 팀 매칭 & 경기장 예약 앱에 AI/ML 기능을 통합해 백엔드 개발자 포트폴리오 경쟁력 강화  
**핵심 어필 포인트**: AI 서비스 통합 설계 경험 (추천 엔진 + LLM 챗봇)

---

## 1. 목표

- **팀/매치 추천 엔진**: 유저 프로필 기반 content-based filtering으로 적합한 팀·매치 자동 추천
- **AI 풋살 어시스턴트 챗봇**: Claude API 기반 개인화 챗봇 (팀 조언, 경기장 추천, 개인 피드백)

---

## 2. 전체 아키텍처

```
[Browser]
    ↓
[Spring MVC (Java)] ← 기존 코드 유지
    ├── RestTemplate → [Python FastAPI 서버 :8000] → scikit-learn 추천 모델
    └── HttpClient  → [Claude API]                 → 챗봇 & 개인화 피드백
```

**원칙**: 기존 Spring 코드 최소 변경, 신규 기능만 추가

---

## 3. 추천 엔진 (Python FastAPI)

### 3-1. 디렉토리 구조

```
ai-service/
├── main.py              # FastAPI 앱 진입점
├── recommender.py       # content-based filtering 모델
├── data_generator.py    # 합성 데이터 생성
└── requirements.txt     # fastapi, uvicorn, scikit-learn, pandas, numpy
```

### 3-2. 알고리즘

- **방식**: Content-Based Filtering + 코사인 유사도
- **유저 특성**: `preferredPosition`, `gender`, `grade` (실력레벨) — UserDTO 실제 필드 기반
- **매치 필터링**: `minGrade <= user.grade <= maxGrade`, `gender` 호환 여부
- **출력**: 상위 5개 매치 ID 목록

```
UserDTO (preferredPosition, gender, grade)
    ↓
MatchDTO (minGrade, maxGrade, gender, region, startHour) 와 매칭
    ↓ grade 범위 필터 → gender 필터 → 코사인 유사도 정렬
상위 5개 반환
```

> **주의**: UserDTO에 지역(region) 필드 없음. 매치의 `region` 필드로 1차 필터 불가, 대신 grade·gender·position 기반 매칭 후 region을 가중치로 활용

### 3-3. API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 서버 상태 확인 |
| POST | `/recommend/teams` | 팀 추천 |
| POST | `/recommend/matches` | 매치 추천 |

### 3-4. 데이터 부족 해결 전략

- 서버 초기 기동 시 **합성 데이터 300건 자동 생성** (실제 DB 지역명·포지션 Enum 기반)
- 매치 완료 시 실데이터로 점진적 교체
- 신규 유저(Cold-start) → 지역 기반 기본 추천으로 fallback

### 3-5. Spring 연동

**새로 추가할 파일**:
- `RecommendService.java` — FastAPI 호출 및 결과 가공
- `RecommendController.java` — `/match/recommend` 엔드포인트

```java
// RecommendService
@Service
public class RecommendService {
    private final RestTemplate restTemplate;

    public List<MatchDTO> getRecommendedMatches(UserDTO user) {
        // FastAPI로 유저 프로필 POST → 추천 ID 목록 수신
        // ID로 DB에서 실제 MatchDTO 조회 후 반환
    }
}
```

**Fallback 처리**: FastAPI 서버 다운 시 최신 매치 목록으로 대체

---

## 4. AI 챗봇 (Claude API)

### 4-1. 연동 구조

```
[플로팅 채팅 UI (JSP + AJAX)]
    ↓ POST /ai/chat
[ChatController (Spring)]
    ↓ HTTPS POST (HttpClient)
[Claude API — claude-sonnet-4-6]
    ↑ 시스템 프롬프트에 유저 컨텍스트 주입
```

### 4-2. 시스템 프롬프트

```
당신은 풋살 전문 AI 어시스턴트입니다.
현재 유저 정보:
- 닉네임: {nickname}
- 선호 포지션: {preferredPosition}
- 소속 팀: {teamName} (없으면 "팀 없음")
- 최근 매치 기록: {최근 3건 요약}

이 정보를 바탕으로 개인화된 조언을 제공하세요.
풋살과 무관한 질문은 정중히 거절하세요.
```

### 4-3. 제공 기능

| 기능 | 예시 질문 | 응답 방식 |
|------|-----------|-----------|
| 팀 구성 조언 | "우리 팀 포워드가 부족해" | 포지션별 보완 전략 제안 |
| 경기장 추천 | "강남 근처 경기장 어때?" | DB 경기장 데이터 기반 |
| 개인 피드백 | "내 최근 경기 어때?" | 매치 기록 분석 후 조언 |

### 4-4. Spring 구현

**새로 추가할 파일**:
- `AiService.java` — Claude API 호출 및 프롬프트 구성
- `ChatController.java` — `/ai/chat` REST 엔드포인트
- `ChatRequestDTO.java` — 요청 DTO

**대화 기록**: 세션에 유지 (DB 저장 없음, 구현 단순화)

### 4-5. UI

- 로그인 유저에게만 표시되는 **우측 하단 플로팅 채팅 버튼**
- `header.jsp`에 공통 위젯으로 추가
- AJAX 비동기 호출로 페이지 전환 없이 동작

---

## 5. 개발 순서

| Phase | 기간 | 내용 |
|-------|------|------|
| Phase 1 | 1~2일 | Python FastAPI 서버 세팅, 합성 데이터 생성 |
| Phase 2 | 2~3일 | 추천 엔진 구현 & Spring 연동 |
| Phase 3 | 1~2일 | Claude API 챗봇 구현 |
| Phase 4 | 1일 | UI 통합, 에러 핸들링, README 작성 |

---

## 6. 에러 핸들링 & Fallback

| 장애 상황 | 처리 방식 |
|-----------|-----------|
| FastAPI 서버 다운 | 최신 매치 목록으로 대체, 에러 메시지 없이 자연스럽게 |
| Claude API 오류 | "잠시 후 다시 시도해주세요" 안내 |
| Cold-start 유저 | 지역 기반 기본 추천 |

---

## 7. 포트폴리오 어필 포인트

- **마이크로서비스 아키텍처**: Spring + Python FastAPI 이종 서비스 연동
- **AI 서비스 통합 설계**: LLM 컨텍스트 주입 전략, 개인화 프롬프트 설계
- **데이터 부족 문제 해결**: 합성 데이터 생성 전략 + Cold-start fallback
- **안정성 설계**: AI 서비스 장애 시 Fallback 처리

---

## 8. 보안 & 환경 변수

### API Key 관리
- Claude API Key: 환경변수 `CLAUDE_API_KEY`로 관리
- `application-secret.properties` 파일 분리 (.gitignore 등록)
- 운영 시 AWS Secrets Manager / Spring Cloud Config 사용 예정

### 입력 검증
- 메시지 길이 제한: 500자
- XSS 방지: `Spring HtmlUtils.htmlEscape()`
- SQL Injection 방지: PreparedStatement (기본 적용)

---

## 9. 비용 통제

### Rate Limiting
- 유저당 챗봇 호출: 일 30회 제한
- 동시 요청: 유저당 1건 (중복 클릭 방지)

### 토큰 최적화
- 시스템 프롬프트: 약 500토큰 고정
- 매치 기록: 최근 3건만 요약 (전체 X)
- 경기장 정보: "경기장" 키워드 포함 시에만 컨텍스트 추가 (동적 주입)

### 예상 비용
- 유저 10명 × 30회/일 × 30일 = 9,000 호출/월
- 평균 토큰 2,000 → 약 $50~80/월 예상

---

## 10. 추천 품질 검증

### 정성적 평가 (현 단계)
- 합성 데이터 기반이므로 정량적 평가 불가
- 의도한 매칭 패턴 반영 여부 수동 검증
  - 테스트 케이스: 초급 유저 → 초급 매치만 추천되는가?
  - 테스트 케이스: 여성 매치 가능 유저 → 여성/혼성 매치 우선 추천되는가?

### 정량적 평가 (실서비스 데이터 수집 후)
- Precision@5: 추천된 5개 중 실제 신청한 매치 비율
- 재방문율: 추천 후 매치 신청까지 이어진 비율

---

## 11. 기술 의사결정

| 선택 | 대안 | 선택 이유 |
|------|------|-----------|
| FastAPI | Flask, Django | 비동기 지원, 자동 API 문서, 타입 검증 |
| Content-Based | Collaborative Filtering | 데이터 부족 시 적합, Cold-start 강함 |
| Claude Sonnet | GPT-4, Gemini | 한국어 자연스러움, 안전 가이드라인 강함 |
| 세션 저장 | DB 저장 | MVP 단계 단순화, 확장 시 마이그레이션 가능 |
| Python 분리 | Spring 단일 | ML 라이브러리 생태계, 책임 분리 |
