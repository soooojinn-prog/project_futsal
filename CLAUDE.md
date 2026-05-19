# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**letsfutsal** — 풋살 팀 매칭 및 경기장 예약 웹 애플리케이션. Spring MVC + MyBatis + MySQL + JSP 기반의 Maven WAR 프로젝트.

## Build & Run

```bash
# 빌드 (코드 포맷 적용 포함)
mvn package

# 포맷만 적용
mvn spotless:apply

# 포맷 검사만 (변경 없이)
mvn spotless:check
```

- 배포: Tomcat에 `target/letsfutsal.war` 배포
- DB: `localhost:3306/letsfutsal` (user: `letsfutsal` / pw: `letsfutsal`)
- DB 초기화 스크립트: `sql/letsfutsal_init.sql`, 샘플 데이터: `sql/letsfutsal_sample.sql`

## Architecture

### Spring 컨텍스트 구조
- `AppInitializer` — `DispatcherServlet` 등록 (web.xml 대신 Java Config)
- `RootConfig` — DataSource(HikariCP), MyBatis SqlSessionFactory, TransactionManager, ObjectMapper
- `WebConfig` — MVC 설정, ViewResolver (`/WEB-INF/views/*.jsp`), 정적 리소스 (`/resources/**`)

### 레이어 구조
```
Controller → Service → Mapper(interface) → MyBatis XML → MySQL
```
- **Controller**: `src/main/java/.../[domain]/[Domain]Controller.java`
- **Service**: 인터페이스(`IXxxService`) + 구현체(`XxxService`) 쌍으로 구성 (board, stadium 제외)
- **Mapper**: `src/main/java/.../mapper/[Domain]Mapper.java` (인터페이스)
- **MyBatis XML**: `src/main/resources/mybatis/mapper_[domain].xml`
- **DTO**: `src/main/java/.../dto/` — 모든 도메인 DTO 집중 관리
- **View**: `src/main/webapp/WEB-INF/views/[domain]/*.jsp`

### 도메인 목록
`user`, `team`, `match`, `stadium`, `board`(자유게시판), `rank`, `ai`(챗봇 + RAG)

### 인증
- `LoginInterceptor` — 세션의 `loginUser` 속성으로 로그인 여부 확인, 미로그인 시 `/user/login` 리다이렉트
- 세션 키: `loginUser` (UserDTO 객체)
- **주의**: 비밀번호가 평문 저장됨 (`UserService.register` 참고) — 암호화 미구현 상태

### AI 기능 구조

챗봇은 **하이브리드 라우터 + RAG** 구조 — 풋살 지식 질문은 Python ai-service의 RAG 파이프라인으로, 개인 조언은 Spring에서 Claude API 직접 호출.

```
[브라우저 챗봇 위젯] → POST /ai/chat → ChatController → AiService.chat()
   │
   ├─ IntentRouter.route(message)
   │   ├─ keyword 사전(오프사이드, 포메이션, 압박 등) 직격 → KNOWLEDGE
   │   └─ keyword miss → RagClient.classify() (Python /router/classify, Claude Tool Use)
   │
   ├─ KNOWLEDGE → RagClient.askRag() → Python /chat/rag → ChromaDB 검색 + Claude 답변 + citation
   │             실패 시 chatAdvice()로 폴백
   └─ ADVICE → chatAdvice() → Claude API 직접 호출 (개인화 시스템 프롬프트)
```

- **Spring 측**: `ai/AiService.java`, `ai/ChatController.java`, `ai/IntentRouter.java`, `ai/RagClient.java`, `ai/RecommendService.java`
- **DTO**: `dto/ChatRequestDTO.java`, `dto/ChatResponseDTO.java` (`message`/`mode`/`citations`), `dto/CitationDTO.java`
- **Python ai-service** (`ai-service/`): FastAPI + LangChain + ChromaDB + sentence-transformers(`jhgan/ko-sroberta-multitask`) + LangGraph + Anthropic SDK. 자세한 구조·실행·평가는 [`ai-service/README.md`](ai-service/README.md) 참고.
- **환경 변수**: `CLAUDE_API_KEY` (Spring·Python 공유), `AI_SERVICE_URL` (기본 `http://localhost:8000`), `SPRING_BASE_URL` (Python에서 Spring 호출용)
- **레이트 리미트**: 챗봇 세션당 일일 30회 (`ChatController.DAILY_LIMIT`)

**LangGraph 에이전트** (`/ai/coordinator` 페이지)

자연어 요청을 별도 페이지에서 받아 LangGraph StateGraph로 처리:

```
사용자 입력 → parse_intent (Claude Tool Use) → conditional edge
  ├─ SINGLE      → single_stadium → single_team → single_match → review
  └─ TOURNAMENT  → ThreadPoolExecutor로 Stadium/Team/MatchAgent 병렬 → tournament_assemble
→ summarize → ProposalDTO 응답 → 사용자 편집 → /ai/agent/confirm → DB INSERT
```

- **Spring 측**: `ai/AgentController.java`, `ai/AgentService.java`, `ai/AgentDataController.java` (에이전트용 read-only API), `dto/AgentRequestDTO.java`, `dto/ProposalDTO.java`, `dto/MatchProposalDTO.java`, `dto/BracketDTO.java`, `dto/ConfirmRequestDTO.java`
- **Python ai-service** (`ai-service/agent/`): LangGraph 0.2 + Tool 6개 + StateGraph + 3개 sub-agent
- **인증**: `/api/agent-data/**`는 인터셉터 영향 없음 (내부 호출용 read-only)

### MyBatis 설정 특이사항
- `mapUnderscoreToCamelCase=true` — DB 컬럼 `snake_case` → Java 필드 `camelCase` 자동 변환
- DB ENUM 컬럼은 커스텀 TypeHandler로 처리: `Gender`, `Match`, `EntityType`, `PreferredPosition`

## Code Style

- Spotless + Eclipse formatter (`eclipse-formatter.xml`) 자동 적용 (빌드 시 `compile` 단계)
- 들여쓰기: 스페이스 2칸, 라인 엔딩: CRLF (Windows)
- JSP는 Spotless 미지원 — 수동 포맷
- Java 21, Jakarta EE (Servlet 6.1, JSP 4.0)
