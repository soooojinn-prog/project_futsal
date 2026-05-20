# ML 풋살 자세 분석기 설계 (Feature 1)

> 포트폴리오·취업 목적 AI 기능 확장 — 기능 1 (ML / 컴퓨터 비전)
> 작성일: 2026-05-20
> 관련 로드맵: [docs/ai-features-roadmap.md](../../ai-features-roadmap.md)
> 선행 기능: [기능 2 RAG 챗봇](2026-05-19-rag-chatbot-design.md), [기능 3 LangGraph 에이전트](2026-05-19-langgraph-agent-design.md)

---

## 1. 목표 및 배경

기능 2(RAG)와 기능 3(LangGraph)으로 LLM·Agent·RAG 영역은 커버되었다. 본 기능은 마지막으로 **ML/컴퓨터 비전** 영역을 채워 이력서 7개 기술(LLM API, Agent, LangChain, LangGraph, 멀티에이전트, RAG, ML/CV)을 모두 다룬다.

사용자가 풋살 킥/드리블 영상을 업로드하면:

1. OpenCV로 프레임 추출 + MediaPipe로 33개 관절 좌표 추출
2. 관절 각도·상대 위치 feature engineering
3. 사전 학습된 분류 모델로 자세 4분류 (킥 좋음/나쁨, 드리블 좋음/나쁨)
4. 핵심 관절 각도 통계
5. Claude API로 자연어 피드백 자동 생성 ("무릎이 너무 잠겨 있어요...")

학습 단계에서는 RandomForest와 PyTorch MLP를 모두 학습·비교한 뒤 더 우수한 모델 1개를 서비스에 배포한다.

**이력서 문구 후보**

> AI Hub 스포츠 자세 데이터셋 + MediaPipe 33개 관절 추출 + scikit-learn RandomForest와 PyTorch MLP를 정확도·추론 속도로 비교 후 최종 모델 선정. 풋살 킥/드리블 자세 4분류 모델을 FastAPI로 서빙, Claude에 분류 결과·핵심 각도 전달하여 사용자 친화 자연어 피드백 자동 생성. end-to-end 영상 처리 latency 측정 포함.

---

## 2. 의사결정 요약

| 항목 | 결정 | 근거 |
|---|---|---|
| 스코프 | 4 분류 (킥 GOOD/BAD + 드리블 GOOD/BAD), 7~10일 | 면접 임팩트와 구현 일정의 균형 |
| 입력 방식 | 영상 파일 업로드 (≤ 30초 mp4) | 웹캠 실시간은 WebSocket·MediaPipe JS 부담, YAGNI |
| 데이터 | AI Hub "스포츠 자세 영상" 데이터셋 | 공공 데이터 활용 면접 임팩트, 라벨링 자동 |
| Feature | 관절 각도 12개 + 상대 위치 (handcraft) | 작은 데이터셋에 신경망보다 효과적, 면접 설명 쉬움 |
| 학습 모델 | RandomForest + PyTorch MLP 둘 다 | 모델 비교 능력 어필 |
| 서비스 모델 | 정확도·F1·추론 속도 비교 후 **최종 1개만** 배포 | 운영 단순화, "모델 선택 근거" 면접 설명 가능 |
| LLM 결합 | Claude로 자연어 피드백 생성 | ML+LLM 결합 임팩트, RAG·LangGraph와 시너지 |
| 통합 | Python `ai-service`에 `pose/` 패키지 추가 | 기존 FastAPI 재활용 |
| 평가 | 정확도·F1·추론 시간·전체 latency 4지표 | 모델 + 운영 양쪽 측정 |
| 어필 요소 | 모델 비교 리포트 + confusion matrix + 실측 latency | 포트폴리오 정량 자료 풍부 |

---

## 3. 아키텍처

### 3.1 전체 흐름

```
[브라우저: /ai/pose 페이지]
       │  사용자가 mp4 영상 업로드 (≤ 30초)
       ▼ POST /ai/pose/analyze (multipart/form-data)
[Spring PoseController]
       │ 1. 로그인·rate-limit (일일 10회)
       │ 2. 영상 크기·길이 검증
       ▼ Python으로 영상 byte stream 전달
[Python FastAPI /pose/analyze]
       │
       ▼
┌──────────────────────────────────────────────────┐
│  start_time = now()                              │
│                                                   │
│  1. PoseExtractor (extractor.py)                 │
│     - OpenCV cv2.VideoCapture                    │
│     - 10fps로 프레임 샘플링 (≤ 300 프레임)        │
│     - MediaPipe Pose → 프레임당 33점 좌표         │
│                                                   │
│  2. FeatureBuilder (features.py)                 │
│     - 관절 각도 12개 계산                          │
│       (무릎, 발목, 엉덩이, 어깨 좌우)             │
│     - 상대 위치 (몸 중심 기준 정규화)              │
│     - 프레임별 feature vector 평균 + 표준편차     │
│                                                   │
│  3. PoseClassifier (classifier.py)               │
│     - 최종 선정 모델 로드 (RF 또는 MLP, joblib/pt)│
│     - 4 클래스 예측 + softmax 확률                │
│                                                   │
│  4. KeyAngleStats                                │
│     - 무릎·발목 각도 평균·최소·최대 추출           │
│                                                   │
│  5. FeedbackGenerator (feedback.py)              │
│     - Claude API 호출 (시스템 프롬프트 +         │
│       분류명·확률·핵심 각도)                       │
│     - 자연어 피드백 + 개선 팁 반환                 │
│                                                   │
│  total_processing_ms = now() - start_time        │
└──────────────────────────────────────────────────┘
       │
       ▼ PoseAnalysisResponse JSON
[Spring → 브라우저]
   { pose_class, confidence, key_angles, feedback,
     timing_ms: { frame_extract, mediapipe, classify,
                  feedback, total } }
```

### 3.2 컴포넌트 분리

**Python `ai-service/pose/`** — 신규 패키지

- `extractor.py` — `PoseExtractor` 클래스: 영상 → 프레임 → 33점 좌표 리스트
- `features.py` — `FeatureBuilder`: 33점 → 관절 각도 12 + 상대 위치 → feature vector
- `classifier.py` — `PoseClassifier`: 모델 1개 로드 + 예측 + 확률 + 클래스명 매핑
- `feedback.py` — `FeedbackGenerator`: 분류 결과 + 핵심 각도 → Claude 자연어 피드백
- `schemas.py` — Pydantic DTO (PoseAnalysisResponse, KeyAngles, TimingMs 등)
- `train.py` — CLI: 데이터 로드 → RF/MLP 학습 → 평가 → 더 우수한 모델 1개를 `models/best.joblib`(또는 `best.pt`)로 저장
- `compare.py` — CLI: 두 모델을 분리해 학습·평가 → 비교 리포트 산출 (모델 선정 근거)

**데이터 디렉토리**

- `ai-service/data/pose_raw/` — AI Hub 원본 영상·라벨 (gitignore)
- `ai-service/data/pose_features.csv` — 추출된 feature + 라벨 (재학습용, gitignore)
- `ai-service/models/best.joblib` 또는 `best.pt` — 서비스 모델 (gitignore)
- `ai-service/models/model_card.md` — 모델 선정 근거·지표 (커밋)

**Java (`src/main/java/.../ai/`)**

- `PoseController.java` — `/ai/pose` (GET, 페이지), `/ai/pose/analyze` (POST, multipart)
- `PoseService.java` — Python에 영상 byte 전달 (RestTemplate multipart)
- `dto/PoseAnalysisDTO.java` — `{ poseClass, confidence, keyAngles, feedback, timingMs }`
- `dto/KeyAnglesDTO.java`, `dto/TimingMsDTO.java` — nested DTO

**View**

- `WEB-INF/views/ai/pose.jsp` — 업로드 + 결과 카드 + 각도 차트 + 자연어 피드백
- `resources/script/pose_analyzer.js` — fetch + 차트 렌더링

**평가**

- `eval/pose_compare.py` — 모델 비교 (RF vs MLP 정확도·F1·추론 시간·confusion matrix)
- `eval/run_pose_eval.py` — 최종 서비스 모델의 end-to-end 평가
- `eval/pose_test_videos/` — 테스트 영상 10~20개 (라벨 포함, gitignore)
- `eval/pose_report_<timestamp>.md` — 평가 리포트 (커밋)

---

## 4. 데이터 흐름 & DTO 계약

### 4.1 Spring ↔ 브라우저

**POST `/ai/pose/analyze`**
- Content-Type: `multipart/form-data`
- Body: `file=<mp4 binary>`

**Response (PoseAnalysisDTO)**
```json
{
  "poseClass": "BAD_KICK_KNEE_LOCKED",
  "className": "킥 — 무릎 잠김",
  "confidence": 0.87,
  "classProbabilities": {
    "GOOD_KICK": 0.05,
    "BAD_KICK_KNEE_LOCKED": 0.87,
    "GOOD_DRIBBLE": 0.04,
    "BAD_DRIBBLE_OVERREACH": 0.04
  },
  "keyAngles": {
    "leftKnee":   { "mean": 168.2, "min": 158.0, "max": 175.0 },
    "rightKnee":  { "mean": 145.0, "min": 130.0, "max": 160.0 },
    "leftAnkle":  { "mean": 90.5,  "min": 82.0,  "max": 100.0 },
    "rightAnkle": { "mean": 92.1,  "min": 85.0,  "max": 99.0  }
  },
  "feedback": "무릎이 너무 펴진 상태에서 임팩트되고 있어요. 30도 정도 더 굽히면 볼 컨트롤이 안정됩니다. 디딤발 발목 각도는 적절하니 그대로 유지하세요.",
  "timingMs": {
    "frameExtract": 420,
    "mediapipe": 1850,
    "classify": 12,
    "feedback": 1200,
    "total": 3500
  }
}
```

### 4.2 Spring ↔ Python (신규 내부 API)

**POST `/pose/analyze`** — multipart 또는 JSON(base64 영상 byte)
- 입력: 영상 file
- 출력: 위 JSON 동일

### 4.3 4 분류 클래스

| 클래스 코드 | 한글명 | 의미 |
|---|---|---|
| `GOOD_KICK` | 좋은 킥 | 디딤발·임팩트·체중 이동 모두 안정 |
| `BAD_KICK_KNEE_LOCKED` | 킥 — 무릎 잠김 | 임팩트 시 무릎 각도 > 160°, 파워 손실 |
| `GOOD_DRIBBLE` | 좋은 드리블 | 발이 공에 밀착, 자세 안정 |
| `BAD_DRIBBLE_OVERREACH` | 드리블 — 과도 |  발이 공에서 멀어져 컨트롤 실패 |

### 4.4 Feature engineering (12 + N)

**관절 각도 12개** — `arccos`로 세 점 기반 각도 계산
- 좌/우 무릎 (엉덩이-무릎-발목)
- 좌/우 발목 (무릎-발목-발가락)
- 좌/우 엉덩이 (어깨-엉덩이-무릎)
- 좌/우 어깨 (목-어깨-팔꿈치)
- 좌/우 팔꿈치, 좌/우 손목

**상대 위치 N개** — 몸 중심(엉덩이 중점) 기준 정규화 후 주요 관절(발끝·손끝) 좌표

**프레임 시퀀스 → 단일 벡터**
- 각 feature의 평균·표준편차 → 길이 2N (사이즈 약 50~60차원)

---

## 5. 에러 처리

**원칙**: 사용자 영상이 다양한 형식·품질이므로 가드 풍부하게.

| 실패 지점 | 동작 |
|---|---|
| 영상 크기 > 50MB | Spring 400 + "영상은 최대 50MB" |
| 영상 길이 > 30초 | Python 400 + 메시지 |
| MediaPipe가 어떤 프레임에서도 사람 감지 못함 | 400 + "영상에서 사람이 보이지 않아요" |
| 33점 중 일부 누락 (occlusion) | 해당 프레임 스킵, 나머지 평균 사용 |
| feature 벡터 NaN | 0으로 대체 + warning 로그 |
| 모델 로드 실패 (startup) | Fail fast — 서버 부팅 실패 |
| Claude API 실패 | 자연어 피드백을 "분류 결과를 확인해주세요"로 대체 + warning |
| Python `/pose/analyze` 5xx | Spring 500 + 사용자에게 "잠시 후 다시 시도" |
| Rate limit (일일 10회) | Spring 429 |

**타임아웃**
- Spring → Python: connect 5s, read 60s (영상 처리 5~30s)
- Python → Claude: 10s
- 전체 hard timeout: 90s

---

## 6. 평가 설계

### 6.1 모델 비교 평가 — `eval/pose_compare.py`

학습 데이터 80% / 테스트 데이터 20% split. 두 모델 동시 학습·평가:

| 지표 | 정의 | RF 목표 | MLP 목표 |
|---|---|---|---|
| `accuracy` | 테스트셋 정확도 | ≥ 0.80 | ≥ 0.75 |
| `f1_macro` | 매크로 F1 | ≥ 0.75 | ≥ 0.70 |
| `inference_time_per_frame_ms` | 1 프레임 추론 시간 | ≤ 5ms | ≤ 10ms |
| `model_size_mb` | 모델 파일 크기 | — | — |

산출물:
- `eval/pose_model_compare.md` — 비교 리포트 + confusion matrix
- 더 우수한 모델 1개를 `models/best.{joblib,pt}`로 저장
- 선정 근거 `models/model_card.md`에 기록

### 6.2 서비스 평가 — `eval/run_pose_eval.py`

테스트 영상 10~20개에 대해 end-to-end 평가:

| 지표 | 정의 | 목표 |
|---|---|---|
| `service_accuracy` | 영상 단위 정확도 (테스트 영상 라벨 vs 예측) | ≥ 0.75 |
| `total_processing_latency_ms` | 영상 업로드 → 응답 완료 평균 | ≤ 5000ms |
| `mediapipe_latency_ms` | MediaPipe만의 시간 | ≤ 3000ms |
| `claude_feedback_latency_ms` | Claude 자연어 피드백 호출 | ≤ 2000ms |
| `feedback_quality` | LLM judge — 피드백이 분류 결과와 일관되며 사용자 친화적인지 (0/1) | ≥ 0.80 |

산출물: `eval/pose_report_<timestamp>.md`

### 6.3 실행

```powershell
cd ai-service
# 모델 비교 (학습 + 평가)
python -m eval.pose_compare --out eval/pose_model_compare.md

# 최종 서비스 평가
python -m eval.run_pose_eval
```

---

## 7. 테스트

**Python (pytest)**
- `tests/test_pose_extractor.py` — Mock OpenCV/MediaPipe로 프레임 추출 검증
- `tests/test_pose_features.py` — 관절 각도 계산 정확도 (알려진 좌표 → 알려진 각도)
- `tests/test_pose_classifier.py` — Mock 모델로 예측 결과 형식 검증
- `tests/test_pose_feedback.py` — Mock Claude로 프롬프트 구성 검증
- `tests/test_pose_endpoint.py` — FastAPI TestClient로 `/pose/analyze` 통합 (Mock everything)

**Java (JUnit)**
- `PoseServiceTest` — RestTemplate multipart mock + 응답 파싱
- `PoseControllerTest` — MockMvc로 401/400/200 분기

**수동 데모 시나리오** (Task 15 통합)
1. 본인이 인사이드 킥 영상 5초 촬영 → 업로드 → "GOOD_KICK" + 자연어 피드백
2. 무릎 펴고 일부러 잘못된 킥 → "BAD_KICK_KNEE_LOCKED"
3. 드리블 영상 → "GOOD_DRIBBLE"
4. 빈 영상(사람 없음) → 400 에러 + 친절 메시지

---

## 8. 파일 변경 목록

### 8.1 Python — 신규 11 / 변경 2

| 경로 | 변경 | 책임 |
|---|---|---|
| `pose/__init__.py` | 신규 | 패키지 마커 |
| `pose/extractor.py` | 신규 | 영상 → 33점 좌표 |
| `pose/features.py` | 신규 | 관절 각도·상대 위치 |
| `pose/classifier.py` | 신규 | 모델 1개 로드·예측 |
| `pose/feedback.py` | 신규 | Claude 자연어 피드백 |
| `pose/schemas.py` | 신규 | Pydantic DTO |
| `pose/train.py` | 신규 | 학습 CLI (RF + MLP) |
| `pose/compare.py` | 신규 | 모델 비교 |
| `eval/pose_compare.py` | 신규 | 학습·비교 평가 |
| `eval/run_pose_eval.py` | 신규 | 서비스 평가 |
| `eval/pose_test_videos/` | 신규 (gitignore) | 테스트 영상 |
| `models/model_card.md` | 신규 | 모델 선정 근거 |
| `main.py` | 변경 | `/pose/analyze` 엔드포인트 추가 + startup에서 모델 로드 |
| `requirements.txt` | 변경 | `mediapipe`, `opencv-python`, `torch`(이미 있음), `scikit-learn`(이미 있음) 추가 |
| `tests/test_pose_*.py` | 신규 | pytest 5종 |

### 8.2 Java — 신규 4 / 변경 0

| 경로 | 변경 | 책임 |
|---|---|---|
| `ai/PoseController.java` | 신규 | 라우트 |
| `ai/PoseService.java` | 신규 | Python multipart 호출 |
| `dto/PoseAnalysisDTO.java` | 신규 | 응답 |
| `dto/KeyAnglesDTO.java`, `dto/TimingMsDTO.java` | 신규 | nested |
| `test/.../PoseServiceTest.java`, `PoseControllerTest.java` | 신규 | JUnit |

### 8.3 View

| 경로 | 변경 |
|---|---|
| `WEB-INF/views/ai/pose.jsp` | 신규 — 업로드 + 결과 시각화 |
| `resources/script/pose_analyzer.js` | 신규 |
| `WEB-INF/views/common/header.jsp` | 변경 — 네비에 "🏃 자세 분석" 메뉴 추가 |

### 8.4 문서

| 경로 | 변경 |
|---|---|
| `docs/superpowers/specs/2026-05-20-pose-analysis-design.md` | 신규 (본 spec) |
| `ai-service/README.md` | 변경 — Pose 섹션 |
| `CLAUDE.md` | 변경 — AI 구조에 추가 |
| `docs/ai-features-roadmap.md` | 변경 — 기능 1 완료 표시 |

---

## 9. 의존성 & 환경

**Python (`requirements.txt` 추가)**
```
mediapipe==0.10.x
opencv-python==4.10.x
```
(`torch`, `scikit-learn`은 RAG·기존 환경에 이미 있음)

**Java** — 신규 의존성 없음 (RestTemplate, Jackson 이미 있음)

**환경 변수**
- 기존 `CLAUDE_API_KEY`, `AI_SERVICE_URL` 그대로
- 신규: 없음

**AI Hub 데이터**
- 가입·승인 1~2일 (Day 1 시작 시 신청)
- 다운로드: `data/pose_raw/` (gitignore)

---

## 10. 일정 (총 7~10일)

| Day | 작업 | 산출물 |
|---|---|---|
| **Day 1** | AI Hub 가입·승인 신청, mediapipe·opencv 설치, `pose/__init__.py` 골격 | requirements.txt 갱신 |
| Day 2 | `extractor.py` — OpenCV + MediaPipe 33점 좌표 추출, 단위 테스트 | 영상 1개 처리 동작 |
| Day 3 | `features.py` — 12 관절 각도 + 상대 위치, 단위 테스트 | feature CSV 1개 생성 |
| **Day 4** | `train.py` + `compare.py` — RF/MLP 학습 + 비교 + `model_card.md` 작성 | 최종 모델 1개 + 비교 리포트 |
| Day 5 | `classifier.py` + `feedback.py` + Python `/pose/analyze` 엔드포인트 + 통합 테스트 | curl로 동작 |
| **Day 6** | Spring `PoseController` + `PoseService` + DTO + JUnit | mvn test 그린 |
| Day 7 | `/ai/pose` JSP 페이지 + 업로드 UI + 결과 시각화 (각도 차트) | 브라우저 데모 |
| **Day 8** | 평가 (`run_pose_eval.py`) + 5 지표 측정 + 리포트 | `pose_report_<ts>.md` |
| Day 9 | 문서 갱신 (README, CLAUDE.md, 로드맵) + 데모 영상 캡처 + 헤더 메뉴 추가 | PR 본문 첨부 |
| Day 10 (예비) | 버그 픽스·UI 다듬기·README 지표 반영 | — |

**Risk**: AI Hub 승인 1~2일. 그동안 mediapipe/opencv 셋업과 코드 골격 진행.

---

## 11. 명시적으로 제외하는 것 (YAGNI)

- 웹캠 실시간 분석 (WebSocket)
- 영상 일괄 분석 (한 번에 여러 개)
- 30초 초과 영상
- 슬로우 모션 재생·스켈레톤 오버레이 동영상
- 사용자별 분석 히스토리 저장
- 모바일 앱 연동
- 자세 교정 동영상 자동 추천
- 학습 데이터 자동 증강 (rotation, mirror 등)
- 모델 비교에서 LightGBM, XGBoost 등 추가 모델

---

## 12. 다음 단계

본 spec 승인 → `superpowers:writing-plans` skill로 전환하여 구현 계획(`docs/superpowers/plans/2026-05-20-pose-analysis.md`) 작성 → 구현 진행.

**선행 작업**: AI Hub "스포츠 자세 영상" 데이터셋 신청 (Day 1 즉시 시작 — 승인까지 1~2일 소요되므로 코드 셋업과 병렬).
