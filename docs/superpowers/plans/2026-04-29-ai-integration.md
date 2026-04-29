# AI 통합 구현 계획 — letsfutsal

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Python FastAPI 추천 엔진 + Claude API 챗봇을 Spring MVC에 통합해 AI 기능이 있는 풋살 앱을 완성한다.

**Architecture:** Spring MVC가 Python FastAPI(포트 8000)를 RestTemplate으로, Claude API를 Java HttpClient로 각각 호출한다. 기존 Spring 코드는 최소 변경하고 `ai` 패키지와 `ai-service/` 폴더만 신규 추가한다.

**Tech Stack:** Python 3.11+, FastAPI 0.115, uvicorn, scikit-learn 1.5, pandas, numpy, pytest / Java 21, Spring MVC 7, Java HttpClient (built-in), RestTemplate (Spring 포함)

---

## 파일 구조 (전체 변경 목록)

**신규 생성 — Python:**
- `ai-service/requirements.txt`
- `ai-service/main.py` — FastAPI 앱 진입점
- `ai-service/data_generator.py` — 합성 매치 데이터 300건 생성
- `ai-service/recommender.py` — content-based filtering 추천 엔진
- `ai-service/tests/__init__.py`
- `ai-service/tests/test_recommender.py` — pytest 테스트

**신규 생성 — Java:**
- `src/main/java/io/github/wizwix/letsfutsal/ai/RecommendService.java`
- `src/main/java/io/github/wizwix/letsfutsal/ai/RecommendController.java`
- `src/main/java/io/github/wizwix/letsfutsal/ai/AiService.java`
- `src/main/java/io/github/wizwix/letsfutsal/ai/ChatController.java`
- `src/main/java/io/github/wizwix/letsfutsal/dto/ChatRequestDTO.java`

**수정 — Java:**
- `src/main/java/io/github/wizwix/letsfutsal/config/RootConfig.java` — RestTemplate 빈 추가

**수정 — JSP:**
- `src/main/webapp/WEB-INF/views/common/header.jsp` — 채팅 위젯 + JS 추가
- `src/main/webapp/WEB-INF/views/match/list.jsp` — AI 추천 섹션 추가

---

## Task 1: Python FastAPI 기본 구조 & /health 엔드포인트

**Files:**
- Create: `ai-service/requirements.txt`
- Create: `ai-service/main.py`

- [ ] **Step 1: ai-service 폴더 생성 및 requirements.txt 작성**

```
ai-service/
```

`ai-service/requirements.txt`:
```
fastapi==0.115.0
uvicorn==0.32.0
scikit-learn==1.5.2
pandas==2.2.3
numpy==1.26.4
pytest==8.3.3
httpx==0.27.2
```

- [ ] **Step 2: 의존성 설치**

```bash
cd ai-service
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Expected: 패키지 설치 완료, 에러 없음

- [ ] **Step 3: main.py 기본 구조 작성 (/health만)**

`ai-service/main.py`:
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="letsfutsal AI Service")


class UserProfile(BaseModel):
    userId: int
    preferredPosition: str
    gender: str  # "MALE", "FEMALE", "ALL"
    grade: int


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: 서버 실행 후 /health 확인**

```bash
uvicorn main:app --reload --port 8000
```

브라우저 또는 curl:
```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status":"ok"}
```

- [ ] **Step 5: 커밋**

```bash
git add ai-service/
git commit -m "feat: Python FastAPI 기본 구조 추가"
```

---

## Task 2: 합성 데이터 생성기 (TDD)

**Files:**
- Create: `ai-service/data_generator.py`
- Create: `ai-service/tests/__init__.py`
- Create: `ai-service/tests/test_data_generator.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`ai-service/tests/__init__.py`: (빈 파일)

`ai-service/tests/test_data_generator.py`:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_generator import generate_matches


def test_generate_returns_correct_count():
    df = generate_matches(300)
    assert len(df) == 300


def test_generate_has_required_columns():
    df = generate_matches(10)
    required = {"matchId", "gender", "minGrade", "maxGrade", "region", "startHour"}
    assert required.issubset(set(df.columns))


def test_grade_range_is_valid():
    df = generate_matches(100)
    assert (df["minGrade"] <= df["maxGrade"]).all()


def test_gender_values_are_valid():
    df = generate_matches(100)
    valid = {"MALE", "FEMALE", "ALL"}
    assert set(df["gender"].unique()).issubset(valid)
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
cd ai-service
pytest tests/test_data_generator.py -v
```

Expected: `ModuleNotFoundError: No module named 'data_generator'`

- [ ] **Step 3: data_generator.py 구현**

`ai-service/data_generator.py`:
```python
import random
import pandas as pd

GENDERS = ["MALE", "FEMALE", "ALL"]
REGIONS = ["서울", "경기", "부산", "대구", "인천", "광주", "대전", "수원"]


def generate_matches(count: int) -> pd.DataFrame:
    records = []
    for i in range(1, count + 1):
        min_grade = random.randint(1, 8)
        max_grade = min(min_grade + random.randint(1, 3), 10)
        records.append({
            "matchId": i,
            "gender": random.choice(GENDERS),
            "minGrade": min_grade,
            "maxGrade": max_grade,
            "region": random.choice(REGIONS),
            "startHour": random.randint(6, 22),
        })
    return pd.DataFrame(records)
```

- [ ] **Step 4: 테스트 재실행 — 통과 확인**

```bash
pytest tests/test_data_generator.py -v
```

Expected: 4 passed

- [ ] **Step 5: 커밋**

```bash
git add ai-service/data_generator.py ai-service/tests/
git commit -m "feat: 합성 매치 데이터 생성기 추가 (TDD)"
```

---

## Task 3: 추천 엔진 (TDD)

**Files:**
- Create: `ai-service/recommender.py`
- Create: `ai-service/tests/test_recommender.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`ai-service/tests/test_recommender.py`:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from data_generator import generate_matches
from recommender import Recommender


@pytest.fixture
def rec():
    return Recommender(generate_matches(300))


def test_recommend_returns_list(rec):
    result = rec.recommend("FW", "MALE", 5)
    assert isinstance(result, list)


def test_recommend_returns_at_most_five(rec):
    result = rec.recommend("FW", "MALE", 5)
    assert len(result) <= 5


def test_recommend_returns_ids_in_grade_range():
    import pandas as pd
    df = pd.DataFrame([
        {"matchId": 1, "gender": "MALE", "minGrade": 1, "maxGrade": 3, "region": "서울", "startHour": 10},
        {"matchId": 2, "gender": "MALE", "minGrade": 5, "maxGrade": 8, "region": "서울", "startHour": 10},
    ])
    rec = Recommender(df)
    result = rec.recommend("FW", "MALE", 2)
    assert 1 in result
    assert 2 not in result


def test_recommend_fallback_when_no_grade_match():
    import pandas as pd
    df = pd.DataFrame([
        {"matchId": 1, "gender": "MALE", "minGrade": 1, "maxGrade": 2, "region": "서울", "startHour": 10},
    ])
    rec = Recommender(df)
    result = rec.recommend("FW", "MALE", 99)
    assert isinstance(result, list)


def test_recommend_gender_filter():
    import pandas as pd
    df = pd.DataFrame([
        {"matchId": 1, "gender": "FEMALE", "minGrade": 1, "maxGrade": 10, "region": "서울", "startHour": 10},
        {"matchId": 2, "gender": "MALE",   "minGrade": 1, "maxGrade": 10, "region": "서울", "startHour": 10},
        {"matchId": 3, "gender": "ALL",    "minGrade": 1, "maxGrade": 10, "region": "서울", "startHour": 10},
    ])
    rec = Recommender(df)
    result = rec.recommend("FW", "MALE", 5)
    assert 1 not in result
    assert 2 in result or 3 in result
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
pytest tests/test_recommender.py -v
```

Expected: `ModuleNotFoundError: No module named 'recommender'`

- [ ] **Step 3: recommender.py 구현**

`ai-service/recommender.py`:
```python
import pandas as pd

GENDER_COMPAT = {
    "MALE":   {"MALE", "ALL"},
    "FEMALE": {"FEMALE", "ALL"},
    "ALL":    {"MALE", "FEMALE", "ALL"},
}


class Recommender:
    def __init__(self, matches: pd.DataFrame):
        self.matches = matches.copy()

    def recommend(self, position: str, gender: str, grade: int, top_n: int = 5) -> list[int]:
        df = self.matches.copy()

        # grade 범위 필터
        grade_filtered = df[(df["minGrade"] <= grade) & (df["maxGrade"] >= grade)]

        # gender 필터
        compat = GENDER_COMPAT.get(gender, {"ALL"})
        gender_filtered = grade_filtered[grade_filtered["gender"].isin(compat)]

        # 필터 후 비어있으면 fallback: 최신 매치 상위 top_n
        if gender_filtered.empty:
            return list(self.matches["matchId"].head(top_n).astype(int))

        # grade 중간값과 유저 grade의 거리로 점수 계산 (가까울수록 높은 점수)
        df2 = gender_filtered.copy()
        df2["gradeMid"] = (df2["minGrade"] + df2["maxGrade"]) / 2
        df2["score"] = 1 / (1 + abs(df2["gradeMid"] - grade))
        top = df2.nlargest(top_n, "score")
        return list(top["matchId"].astype(int))
```

- [ ] **Step 4: 테스트 재실행 — 통과 확인**

```bash
pytest tests/test_recommender.py -v
```

Expected: 5 passed

- [ ] **Step 5: 커밋**

```bash
git add ai-service/recommender.py ai-service/tests/test_recommender.py
git commit -m "feat: content-based filtering 추천 엔진 추가 (TDD)"
```

---

## Task 4: FastAPI 추천 엔드포인트 연결

**Files:**
- Modify: `ai-service/main.py` — startup 이벤트 + /recommend/matches 엔드포인트 추가

- [ ] **Step 1: main.py에 추천 엔드포인트 추가**

`ai-service/main.py` 전체 교체:
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from data_generator import generate_matches
from recommender import Recommender

recommender: Recommender | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global recommender
    matches = generate_matches(300)
    recommender = Recommender(matches)
    yield


app = FastAPI(title="letsfutsal AI Service", lifespan=lifespan)


class UserProfile(BaseModel):
    userId: int
    preferredPosition: str
    gender: str  # "MALE", "FEMALE", "ALL"
    grade: int


class RecommendResponse(BaseModel):
    matchIds: list[int]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/recommend/matches", response_model=RecommendResponse)
def recommend_matches(user: UserProfile):
    if recommender is None:
        return RecommendResponse(matchIds=[])
    ids = recommender.recommend(user.preferredPosition, user.gender, user.grade)
    return RecommendResponse(matchIds=ids)
```

- [ ] **Step 2: 서버 재시작 후 엔드포인트 테스트**

```bash
uvicorn main:app --reload --port 8000
```

```bash
curl -X POST http://localhost:8000/recommend/matches \
  -H "Content-Type: application/json" \
  -d '{"userId":1,"preferredPosition":"FW","gender":"MALE","grade":5}'
```

Expected:
```json
{"matchIds":[42,17,83,156,201]}
```
(ID는 합성 데이터 기반이므로 실행마다 다를 수 있음)

- [ ] **Step 3: 전체 pytest 실행**

```bash
pytest tests/ -v
```

Expected: 9 passed

- [ ] **Step 4: 커밋**

```bash
git add ai-service/main.py
git commit -m "feat: FastAPI 추천 엔드포인트 연결"
```

---

## Task 5: Spring RestTemplate 빈 추가

**Files:**
- Modify: `src/main/java/io/github/wizwix/letsfutsal/config/RootConfig.java`

- [ ] **Step 1: RootConfig.java에 RestTemplate 빈 추가**

`src/main/java/io/github/wizwix/letsfutsal/config/RootConfig.java`의 마지막 `}` 앞에 추가:

```java
  @Bean
  public RestTemplate restTemplate() {
    return new RestTemplate();
  }
```

import 추가 (파일 상단 import 목록에):
```java
import org.springframework.web.client.RestTemplate;
```

- [ ] **Step 2: 빌드 확인**

```bash
mvn spotless:apply && mvn package -DskipTests
```

Expected: `BUILD SUCCESS`

- [ ] **Step 3: 커밋**

```bash
git add src/main/java/io/github/wizwix/letsfutsal/config/RootConfig.java
git commit -m "feat: Spring RestTemplate 빈 등록"
```

---

## Task 6: Spring 추천 서비스 & REST 컨트롤러

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/ai/RecommendService.java`
- Create: `src/main/java/io/github/wizwix/letsfutsal/ai/RecommendController.java`

- [ ] **Step 1: RecommendService.java 작성**

`src/main/java/io/github/wizwix/letsfutsal/ai/RecommendService.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import io.github.wizwix.letsfutsal.match.MatchService;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Service
public class RecommendService {
  private final RestTemplate restTemplate;
  private final MatchService matchService;
  private final String aiServiceUrl;

  public RecommendService(RestTemplate restTemplate, MatchService matchService) {
    this.restTemplate = restTemplate;
    this.matchService = matchService;
    this.aiServiceUrl = System.getenv().getOrDefault("AI_SERVICE_URL", "http://localhost:8000");
  }

  public List<MatchDTO> getRecommendedMatches(UserDTO user) {
    try {
      Map<String, Object> request = Map.of(
          "userId", user.getUserId(),
          "preferredPosition", user.getPreferredPosition() != null ? user.getPreferredPosition() : "FW",
          "gender", user.getGender() != null ? user.getGender().name() : "ALL",
          "grade", user.getGrade());

      @SuppressWarnings("unchecked")
      Map<String, Object> response = restTemplate.postForObject(
          aiServiceUrl + "/recommend/matches", request, Map.class);

      if (response == null || !response.containsKey("matchIds")) {
        return getFallbackMatches();
      }

      @SuppressWarnings("unchecked")
      List<Integer> matchIds = (List<Integer>) response.get("matchIds");
      return matchIds.stream()
          .map(id -> matchService.getMatchById(id.longValue()))
          .filter(m -> m != null)
          .toList();
    } catch (Exception e) {
      return getFallbackMatches();
    }
  }

  private List<MatchDTO> getFallbackMatches() {
    return matchService.getMatchList("all", null, null, null, null, null, null, null);
  }
}
```

- [ ] **Step 2: RecommendController.java 작성**

`src/main/java/io/github/wizwix/letsfutsal/ai/RecommendController.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/ai")
public class RecommendController {
  private final RecommendService recommendService;

  public RecommendController(RecommendService recommendService) {
    this.recommendService = recommendService;
  }

  @GetMapping("/recommend/matches")
  public ResponseEntity<List<MatchDTO>> recommendMatches(HttpSession session) {
    UserDTO user = (UserDTO) session.getAttribute("loginUser");
    if (user == null) {
      return ResponseEntity.ok(List.of());
    }
    return ResponseEntity.ok(recommendService.getRecommendedMatches(user));
  }
}
```

- [ ] **Step 3: 빌드 확인**

```bash
mvn spotless:apply && mvn package -DskipTests
```

Expected: `BUILD SUCCESS`

- [ ] **Step 4: 동작 확인 (Tomcat 배포 후)**

Python FastAPI 서버가 8000포트에서 실행 중인 상태에서, 로그인 후:
```
GET http://localhost:8080/letsfutsal/ai/recommend/matches
```

Expected: 매치 DTO JSON 배열 반환 (FastAPI 다운 시 빈 배열 또는 일반 매치 목록)

- [ ] **Step 5: 커밋**

```bash
git add src/main/java/io/github/wizwix/letsfutsal/ai/
git commit -m "feat: Spring 추천 서비스 & REST 컨트롤러 추가"
```

---

## Task 7: Claude API 챗봇 서비스

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/dto/ChatRequestDTO.java`
- Create: `src/main/java/io/github/wizwix/letsfutsal/ai/AiService.java`
- Create: `src/main/java/io/github/wizwix/letsfutsal/ai/ChatController.java`

- [ ] **Step 1: ChatRequestDTO.java 작성**

`src/main/java/io/github/wizwix/letsfutsal/dto/ChatRequestDTO.java`:
```java
package io.github.wizwix.letsfutsal.dto;

public class ChatRequestDTO {
  private String message;

  public String getMessage() {
    return message;
  }

  public void setMessage(String message) {
    this.message = message;
  }
}
```

- [ ] **Step 2: AiService.java 작성**

`src/main/java/io/github/wizwix/letsfutsal/ai/AiService.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import org.springframework.stereotype.Service;
import org.springframework.web.util.HtmlUtils;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.List;

@Service
public class AiService {
  private static final String CLAUDE_API_URL = "https://api.anthropic.com/v1/messages";
  private static final int MAX_MESSAGE_LENGTH = 500;

  private final HttpClient httpClient = HttpClient.newHttpClient();
  private final ObjectMapper objectMapper;
  private final String apiKey;

  public AiService(ObjectMapper objectMapper) {
    this.objectMapper = objectMapper;
    this.apiKey = System.getenv("CLAUDE_API_KEY");
  }

  public String chat(UserDTO user, String rawMessage, List<MatchDTO> recentMatches) {
    if (apiKey == null || apiKey.isBlank()) {
      return "AI 서비스가 설정되지 않았습니다.";
    }

    String message = rawMessage.length() > MAX_MESSAGE_LENGTH
        ? rawMessage.substring(0, MAX_MESSAGE_LENGTH)
        : rawMessage;
    message = HtmlUtils.htmlEscape(message);

    try {
      String requestBody = buildRequestBody(buildSystemPrompt(user, recentMatches), message);
      HttpRequest request = HttpRequest.newBuilder()
          .uri(URI.create(CLAUDE_API_URL))
          .header("Content-Type", "application/json")
          .header("x-api-key", apiKey)
          .header("anthropic-version", "2023-06-01")
          .POST(HttpRequest.BodyPublishers.ofString(requestBody))
          .build();

      HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
      return parseResponse(response.body());
    } catch (Exception e) {
      return "잠시 후 다시 시도해주세요.";
    }
  }

  private String buildSystemPrompt(UserDTO user, List<MatchDTO> recentMatches) {
    StringBuilder sb = new StringBuilder();
    sb.append("당신은 풋살 전문 AI 어시스턴트입니다.\n");
    sb.append("현재 유저 정보:\n");
    sb.append("- 닉네임: ").append(user.getNickname()).append("\n");
    sb.append("- 선호 포지션: ").append(
        user.getPreferredPosition() != null ? user.getPreferredPosition() : "없음").append("\n");
    sb.append("- 실력 등급: ").append(user.getGrade()).append("\n");
    if (recentMatches != null && !recentMatches.isEmpty()) {
      sb.append("- 최근 매치: ");
      recentMatches.stream().limit(3).forEach(m ->
          sb.append(m.getMatchDate()).append(" ").append(m.getRegion()).append(" | "));
    }
    sb.append("\n이 정보를 바탕으로 개인화된 풋살 조언을 제공하세요. ");
    sb.append("풋살과 무관한 질문은 정중히 거절하세요.");
    return sb.toString();
  }

  private String buildRequestBody(String systemPrompt, String userMessage) throws Exception {
    String systemJson = objectMapper.writeValueAsString(systemPrompt);
    String messageJson = objectMapper.writeValueAsString(userMessage);
    return String.format(
        "{\"model\":\"claude-sonnet-4-6\",\"max_tokens\":1024,\"system\":%s,\"messages\":[{\"role\":\"user\",\"content\":%s}]}",
        systemJson, messageJson);
  }

  private String parseResponse(String responseBody) throws Exception {
    var root = objectMapper.readTree(responseBody);
    var content = root.path("content");
    if (content.isArray() && content.size() > 0) {
      return content.get(0).path("text").asText("잠시 후 다시 시도해주세요.");
    }
    return "잠시 후 다시 시도해주세요.";
  }
}
```

- [ ] **Step 3: ChatController.java 작성 (Rate Limiting 포함)**

`src/main/java/io/github/wizwix/letsfutsal/ai/ChatController.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.ChatRequestDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/ai")
public class ChatController {
  private static final int DAILY_LIMIT = 30;
  private static final String COUNT_KEY = "aiChatCount";
  private static final String DATE_KEY = "aiChatDate";

  private final AiService aiService;

  public ChatController(AiService aiService) {
    this.aiService = aiService;
  }

  @PostMapping("/chat")
  public ResponseEntity<Map<String, String>> chat(
      @RequestBody ChatRequestDTO req,
      HttpSession session) {
    UserDTO user = (UserDTO) session.getAttribute("loginUser");
    if (user == null) {
      return ResponseEntity.status(401).body(Map.of("error", "로그인이 필요합니다."));
    }
    if (req.getMessage() == null || req.getMessage().isBlank()) {
      return ResponseEntity.badRequest().body(Map.of("error", "메시지를 입력해주세요."));
    }
    if (isRateLimited(session)) {
      return ResponseEntity.status(429).body(Map.of("error", "오늘 사용 한도(30회)에 도달했습니다."));
    }

    String response = aiService.chat(user, req.getMessage(), List.of());
    incrementCount(session);
    return ResponseEntity.ok(Map.of("message", response));
  }

  private boolean isRateLimited(HttpSession session) {
    String today = LocalDate.now().toString();
    if (!today.equals(session.getAttribute(DATE_KEY))) {
      session.setAttribute(DATE_KEY, today);
      session.setAttribute(COUNT_KEY, 0);
    }
    Integer count = (Integer) session.getAttribute(COUNT_KEY);
    return count != null && count >= DAILY_LIMIT;
  }

  private void incrementCount(HttpSession session) {
    Integer count = (Integer) session.getAttribute(COUNT_KEY);
    session.setAttribute(COUNT_KEY, count == null ? 1 : count + 1);
  }
}
```

- [ ] **Step 4: CLAUDE_API_KEY 환경변수 설정**

Windows (PowerShell):
```powershell
$env:CLAUDE_API_KEY = "sk-ant-api03-여기에키입력"
```

Linux/Mac:
```bash
export CLAUDE_API_KEY="sk-ant-api03-여기에키입력"
```

Tomcat 실행 전에 설정해야 함. 재시작 시마다 필요하므로 Tomcat의 `setenv.bat` / `setenv.sh`에 추가 권장.

- [ ] **Step 5: 빌드 확인**

```bash
mvn spotless:apply && mvn package -DskipTests
```

Expected: `BUILD SUCCESS`

- [ ] **Step 6: 동작 확인 (Tomcat 배포 후)**

로그인 상태에서:
```bash
curl -X POST http://localhost:8080/letsfutsal/ai/chat \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"message":"포워드 포지션 훈련 방법 알려줘"}'
```

Expected:
```json
{"message":"풋살 포워드로서 효과적인 훈련 방법을 알려드릴게요..."}
```

- [ ] **Step 7: 커밋**

```bash
git add src/main/java/io/github/wizwix/letsfutsal/ai/ \
        src/main/java/io/github/wizwix/letsfutsal/dto/ChatRequestDTO.java
git commit -m "feat: Claude API 챗봇 서비스 추가 (Rate Limiting 포함)"
```

---

## Task 8: 채팅 위젯 UI

**Files:**
- Modify: `src/main/webapp/WEB-INF/views/common/header.jsp`

- [ ] **Step 1: header.jsp에 채팅 위젯 추가**

`header.jsp`의 `</nav>` 바로 뒤, `<main class="container py-4">` 바로 앞에 삽입:

```jsp
<%-- AI 챗봇 위젯 (로그인 유저에게만 표시) --%>
<c:if test="${not empty loginUser}">
  <div id="ai-chat-widget" style="position:fixed;bottom:24px;right:24px;z-index:9999;">
    <div id="chat-panel" style="display:none;width:340px;height:460px;background:#fff;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.18);display:flex;flex-direction:column;overflow:hidden;">
      <div style="background:var(--primary,#2563eb);color:#fff;padding:14px 18px;font-weight:700;display:flex;justify-content:space-between;align-items:center;">
        <span>⚽ AI 풋살 어시스턴트</span>
        <button onclick="toggleChat()" style="background:none;border:none;color:#fff;font-size:18px;cursor:pointer;">✕</button>
      </div>
      <div id="chat-messages" style="flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;">
        <div class="chat-bubble ai" style="background:#f1f5f9;border-radius:12px 12px 12px 4px;padding:10px 14px;max-width:85%;font-size:14px;">
          안녕하세요 ${loginUser.nickname}님! 풋살 관련 무엇이든 물어보세요 😊
        </div>
      </div>
      <div style="padding:12px;border-top:1px solid #e2e8f0;display:flex;gap:8px;">
        <input id="chat-input" type="text" placeholder="메시지 입력..." maxlength="500"
               style="flex:1;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font-size:14px;"
               onkeydown="if(event.key==='Enter')sendMessage()">
        <button onclick="sendMessage()"
                style="background:var(--primary,#2563eb);color:#fff;border:none;border-radius:8px;padding:8px 14px;cursor:pointer;font-size:14px;">전송</button>
      </div>
    </div>
    <button id="chat-toggle-btn" onclick="toggleChat()"
            style="display:block;width:56px;height:56px;border-radius:50%;background:var(--primary,#2563eb);color:#fff;border:none;font-size:24px;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,0.2);margin-top:8px;">
      ⚽
    </button>
  </div>

  <script>
    let chatOpen = false;
    function toggleChat() {
      chatOpen = !chatOpen;
      document.getElementById('chat-panel').style.display = chatOpen ? 'flex' : 'none';
      document.getElementById('chat-toggle-btn').style.display = chatOpen ? 'none' : 'block';
      if (chatOpen) document.getElementById('chat-input').focus();
    }

    function addBubble(text, isUser) {
      const el = document.createElement('div');
      el.className = 'chat-bubble ' + (isUser ? 'user' : 'ai');
      el.style.cssText = isUser
        ? 'background:#2563eb;color:#fff;border-radius:12px 12px 4px 12px;padding:10px 14px;max-width:85%;align-self:flex-end;font-size:14px;'
        : 'background:#f1f5f9;border-radius:12px 12px 12px 4px;padding:10px 14px;max-width:85%;font-size:14px;';
      el.textContent = text;
      const messages = document.getElementById('chat-messages');
      messages.appendChild(el);
      messages.scrollTop = messages.scrollHeight;
    }

    function sendMessage() {
      const input = document.getElementById('chat-input');
      const msg = input.value.trim();
      if (!msg) return;
      input.value = '';
      addBubble(msg, true);

      fetch(contextPath + '/ai/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: msg})
      })
      .then(res => res.json())
      .then(data => addBubble(data.message || data.error || '오류가 발생했습니다.', false))
      .catch(() => addBubble('연결 오류가 발생했습니다.', false));
    }
  </script>
</c:if>
```

- [ ] **Step 2: Tomcat 재배포 후 동작 확인**

1. 로그인 상태에서 우측 하단 ⚽ 버튼 확인
2. 버튼 클릭 → 채팅 패널 열림
3. 메시지 입력 → 응답 수신 확인
4. 비로그인 상태에서 버튼이 보이지 않는지 확인

- [ ] **Step 3: 커밋**

```bash
git add src/main/webapp/WEB-INF/views/common/header.jsp
git commit -m "feat: AI 풋살 어시스턴트 채팅 위젯 UI 추가"
```

---

## Task 9: 매치 목록 AI 추천 섹션

**Files:**
- Modify: `src/main/webapp/WEB-INF/views/match/list.jsp`

- [ ] **Step 1: list.jsp에 AI 추천 섹션 추가**

`list.jsp`의 `<div class="page-hero">` 바로 앞에 삽입:

```jsp
<%-- AI 추천 섹션 (로그인 유저에게만 표시) --%>
<c:if test="${not empty loginUser}">
  <div id="ai-recommend-section" class="mb-4" style="display:none;">
    <div class="d-flex align-items-center gap-2 mb-3">
      <span style="font-size:20px;">⚽</span>
      <h5 class="mb-0 fw-bold">AI 추천 매치</h5>
      <span class="badge bg-primary" style="font-size:11px;">FOR YOU</span>
    </div>
    <div id="ai-recommend-list" class="row g-3">
      <div class="col-12 text-center text-muted py-3">
        <div class="spinner-border spinner-border-sm me-2" role="status"></div>
        AI가 맞춤 매치를 분석 중입니다...
      </div>
    </div>
    <hr class="mt-4">
  </div>
  <script>
    fetch(contextPath + '/ai/recommend/matches')
      .then(res => res.json())
      .then(matches => {
        if (!matches || matches.length === 0) return;
        const section = document.getElementById('ai-recommend-section');
        const list = document.getElementById('ai-recommend-list');
        section.style.display = 'block';
        list.innerHTML = matches.map(function(m) {
          return '<div class="col-md-4">'
            + '<a href="' + contextPath + '/match/' + m.matchId + '" class="text-decoration-none">'
            + '<div class="card h-100 border-primary" style="border-width:2px;">'
            + '<div class="card-body">'
            + '<div class="d-flex justify-content-between align-items-start mb-2">'
            + '<span class="badge bg-primary">' + (m.matchType || '매치') + '</span>'
            + '<small class="text-muted">' + (m.region || '') + '</small>'
            + '</div>'
            + '<p class="mb-1"><strong>' + (m.stadiumName || '경기장 미정') + '</strong></p>'
            + '<small class="text-muted">' + (m.matchDate || '') + ' | 등급 ' + m.minGrade + '~' + m.maxGrade + '</small>'
            + '</div></div></a></div>';
        }).join('');
      })
      .catch(() => {});
  </script>
</c:if>
```

- [ ] **Step 2: 동작 확인**

1. 로그인 상태에서 `/match` 접속
2. "AI 추천 매치" 섹션이 스피너 후 카드로 표시되는지 확인
3. Python AI 서버 중단 후 섹션이 사라지는지(조용히 fallback) 확인
4. 비로그인 상태에서 섹션 미표시 확인

- [ ] **Step 3: 커밋**

```bash
git add src/main/webapp/WEB-INF/views/match/list.jsp
git commit -m "feat: 매치 목록에 AI 추천 섹션 추가"
```

---

## Task 10: 통합 테스트 & 포맷 정리

**Files:**
- Run: `mvn spotless:apply`
- Run: 전체 시나리오 테스트

- [ ] **Step 1: 코드 포맷 일괄 적용**

```bash
mvn spotless:apply
```

Expected: 에러 없음

- [ ] **Step 2: 최종 빌드**

```bash
mvn package -DskipTests
```

Expected: `BUILD SUCCESS`, `target/letsfutsal.war` 생성

- [ ] **Step 3: Python 전체 테스트**

```bash
cd ai-service
pytest tests/ -v
```

Expected: 9 passed, 0 failed

- [ ] **Step 4: 통합 시나리오 체크리스트**

| 시나리오 | 확인 |
|----------|------|
| 비로그인: 채팅 위젯 미표시 | [ ] |
| 비로그인: AI 추천 섹션 미표시 | [ ] |
| 로그인: 채팅 위젯 표시, 메시지 전송 성공 | [ ] |
| 로그인: 매치 목록 AI 추천 섹션 표시 | [ ] |
| FastAPI 서버 중단: 추천 섹션 조용히 사라짐 | [ ] |
| Claude API 키 없음: "AI 서비스가 설정되지 않았습니다." 표시 | [ ] |
| 빈 메시지 전송: 에러 메시지 표시 | [ ] |

- [ ] **Step 5: 최종 커밋**

```bash
git add -A
git commit -m "feat: AI 통합 기능 완성 (추천 엔진 + 챗봇)"
```

---

## 실행 체크리스트 (매번 서버 시작 시)

```bash
# 1. Python AI 서버 시작
cd ai-service
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --port 8000

# 2. Claude API 키 환경변수 설정 (Tomcat 시작 전)
export CLAUDE_API_KEY="sk-ant-api03-..."

# 3. Tomcat에 letsfutsal.war 배포 후 시작
```
