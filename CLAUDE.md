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
`user`, `team`, `match`, `stadium`, `board`(자유게시판), `rank`

### 인증
- `LoginInterceptor` — 세션의 `loginUser` 속성으로 로그인 여부 확인, 미로그인 시 `/user/login` 리다이렉트
- 세션 키: `loginUser` (UserDTO 객체)
- **주의**: 비밀번호가 평문 저장됨 (`UserService.register` 참고) — 암호화 미구현 상태

### MyBatis 설정 특이사항
- `mapUnderscoreToCamelCase=true` — DB 컬럼 `snake_case` → Java 필드 `camelCase` 자동 변환
- DB ENUM 컬럼은 커스텀 TypeHandler로 처리: `Gender`, `Match`, `EntityType`, `PreferredPosition`

## Code Style

- Spotless + Eclipse formatter (`eclipse-formatter.xml`) 자동 적용 (빌드 시 `compile` 단계)
- 들여쓰기: 스페이스 2칸, 라인 엔딩: CRLF (Windows)
- JSP는 Spotless 미지원 — 수동 포맷
- Java 21, Jakarta EE (Servlet 6.1, JSP 4.0)
