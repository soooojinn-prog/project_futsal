# ML 풋살 자세 분석기 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 풋살 킥/드리블 영상을 업로드하면 MediaPipe 33점 추출 → 자세 4분류 + 관절 각도 통계 + Claude 자연어 피드백을 반환하는 ML 분석 시스템 구현.

**Architecture:** Python `ai-service/pose/` 패키지 신설 (extractor → features → classifier → feedback 파이프라인). 학습 단계는 RandomForest + PyTorch MLP 비교 후 우수 모델 1개 선정·배포. Spring `PoseController`가 multipart 영상 전달 + 결과를 JSP 페이지로 렌더링.

**Tech Stack:** Python 3.12 + MediaPipe + OpenCV + scikit-learn + PyTorch + FastAPI. Java 21 + Spring MVC + RestTemplate + Jackson + JSP.

**Spec:** [docs/superpowers/specs/2026-05-20-pose-analysis-design.md](../specs/2026-05-20-pose-analysis-design.md)

**선행 작업:** AI Hub "스포츠 자세 영상" 데이터셋 신청 (Day 1 시작 즉시, 승인 1~2일). 그동안 코드 골격 진행.

---

## 환경 prefix

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot"
$mvn = "C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.2\plugins\maven\lib\maven3\bin\mvn.cmd"
```

이후 `mvn ...`은 위 변수 설정 + `& $mvn ...`. Python venv는 `ai-service/venv/`.

---

## File Structure

**Python (`ai-service/pose/`)** — 신규 패키지

| 경로 | 책임 |
|---|---|
| `pose/__init__.py` | 패키지 마커 |
| `pose/schemas.py` | Pydantic DTO (PoseAnalysisResponse, KeyAngles, TimingMs 등) |
| `pose/extractor.py` | `PoseExtractor` — OpenCV로 영상 → 프레임 + MediaPipe → 33점 좌표 |
| `pose/features.py` | `FeatureBuilder` — 33점 → 관절 각도 12 + 상대 위치 → feature vector |
| `pose/classifier.py` | `PoseClassifier` — `models/best.joblib` 로드 + 예측 |
| `pose/feedback.py` | `FeedbackGenerator` — 분류 결과 + 각도 → Claude 자연어 피드백 |
| `pose/train.py` | CLI: 데이터 → feature → RF/MLP 학습 → 우수 모델 1개 `models/best.joblib`로 저장 + `model_card.md` 작성 |
| `pose/compare.py` | CLI: RF vs MLP 동시 학습·평가 → 비교 리포트 |

**Eval / Models / Data**

| 경로 | 책임 |
|---|---|
| `eval/pose_compare.py` | RF vs MLP 비교 평가 |
| `eval/run_pose_eval.py` | 서비스 end-to-end 평가 (5지표) |
| `eval/pose_test_videos/` *(gitignore)* | 테스트 영상 10~20개 |
| `models/best.joblib` *(gitignore)* | 서비스 모델 |
| `models/model_card.md` *(커밋)* | 모델 선정 근거·지표 |
| `data/pose_raw/` *(gitignore)* | AI Hub 원본 |
| `data/pose_features.csv` *(gitignore)* | 추출 feature + 라벨 |

**Main / Tests / Requirements**

| 경로 | 책임 |
|---|---|
| `main.py` *(변경)* | `/pose/analyze` 엔드포인트 + startup에서 PoseClassifier 로드 |
| `requirements.txt` *(변경)* | `mediapipe==0.10.x`, `opencv-python==4.10.x` 추가 |
| `tests/test_pose_schemas.py` | DTO |
| `tests/test_pose_extractor.py` | Mock OpenCV/MediaPipe |
| `tests/test_pose_features.py` | 관절 각도 계산 정확도 |
| `tests/test_pose_classifier.py` | Mock 모델 |
| `tests/test_pose_feedback.py` | Mock Claude |
| `tests/test_pose_endpoint.py` | FastAPI TestClient |

**Java (`src/main/java/io/github/wizwix/letsfutsal/`)**

| 경로 | 책임 |
|---|---|
| `dto/PoseAnalysisDTO.java` | `{poseClass, className, confidence, classProbabilities, keyAngles, feedback, timingMs}` |
| `dto/KeyAnglesDTO.java` | `{leftKnee, rightKnee, leftAnkle, rightAnkle}` (각각 mean/min/max) |
| `dto/TimingMsDTO.java` | `{frameExtract, mediapipe, classify, feedback, total}` |
| `ai/PoseService.java` | Python `/pose/analyze` multipart 호출 |
| `ai/PoseController.java` | `/ai/pose` (GET), `/ai/pose/analyze` (POST multipart) |
| `test/.../ai/PoseServiceTest.java` | RestTemplate mock |
| `test/.../ai/PoseControllerTest.java` | MockMvc |

**View / Static**

| 경로 | 책임 |
|---|---|
| `WEB-INF/views/ai/pose.jsp` | 업로드 + 결과 카드 + 각도 차트 + 피드백 |
| `resources/script/pose_analyzer.js` | fetch + 차트 렌더링 |
| `WEB-INF/views/common/header.jsp` *(변경)* | 네비에 "🏃 자세 분석" 메뉴 |

**Docs**

| 경로 | 책임 |
|---|---|
| `ai-service/README.md` *(변경)* | Pose 섹션 |
| `CLAUDE.md` *(변경)* | AI 구조 항목 추가 |
| `docs/ai-features-roadmap.md` *(변경)* | 기능 1 완료 표시 |

---

## Decomposition Principles

- **Python 먼저 완성**: Spring이 Python에 의존. Python `/pose/analyze`가 curl로 동작한 뒤 Java 시작.
- **TDD**: 테스트 가능한 유닛(extractor·features·classifier·feedback)은 실패 테스트 → 구현 → 통과 → commit·push.
- **외부 의존 작업(학습, 영상 처리)** : 자동 테스트 어렵. CLI 검증 명령으로 대체.
- **각 Task 끝에 commit + push** (저장소 컨벤션).
- **AI Hub 승인 대기 동안** Task 0~2 (의존성, schemas, extractor 단위 테스트) 진행 가능.

---

## Task 0: AI Hub 신청 + mediapipe·opencv 의존성 + 패키지 골격

**Files:**
- Modify: `ai-service/requirements.txt`
- Create: `ai-service/pose/__init__.py`
- Create: `ai-service/models/.gitkeep`
- Modify: `ai-service/.gitignore`

- [ ] **Step 1: AI Hub 데이터셋 신청 (즉시)**

브라우저로 https://aihub.or.kr 가입 → "스포츠 자세 영상" 또는 "스포츠 동작" 검색 → 데이터셋 사용 신청. 승인 1~2일. **신청 직후 다음 단계 진행**.

- [ ] **Step 2: requirements.txt에 추가**

`ai-service/requirements.txt` 끝에 추가:
```
mediapipe==0.10.20
opencv-python==4.10.0.84
```

- [ ] **Step 3: 가상환경 설치**

```powershell
cd ai-service
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Expected: mediapipe·opencv 설치 완료 (mediapipe 첫 import 시 모델 자동 다운로드, ~50MB).

- [ ] **Step 4: pose 패키지 골격 + 모델 디렉토리**

`ai-service/pose/__init__.py`:
```python
"""풋살 자세 분석 모듈 — MediaPipe + scikit-learn/PyTorch 분류 + Claude 자연어 피드백."""
```

`ai-service/models/.gitkeep` (빈 파일)

- [ ] **Step 5: .gitignore 갱신**

`ai-service/.gitignore` 끝에 추가:
```
data/pose_raw/
data/pose_features.csv
models/*.joblib
models/*.pt
eval/pose_test_videos/
```

- [ ] **Step 6: import 검증**

```powershell
python -c "import cv2; import mediapipe; import pose; print('OK', cv2.__version__, mediapipe.__version__)"
```
Expected: `OK 4.10.0 0.10.20` 형태.

- [ ] **Step 7: Commit**

```powershell
git add ai-service/requirements.txt ai-service/pose/__init__.py ai-service/models/.gitkeep ai-service/.gitignore
git commit -m "chore(pose): mediapipe·opencv 의존성 + pose 패키지 골격"
git push origin main
```

---

## Task 1: Pydantic schemas

**Files:**
- Create: `ai-service/pose/schemas.py`
- Create: `ai-service/tests/test_pose_schemas.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_pose_schemas.py`:
```python
from pose.schemas import (
    AngleStats,
    KeyAngles,
    PoseAnalysisResponse,
    PoseClass,
    TimingMs,
)


def test_angle_stats():
    a = AngleStats(mean=145.0, min=130.0, max=160.0)
    assert a.mean == 145.0


def test_key_angles():
    k = KeyAngles(
        left_knee=AngleStats(mean=160, min=150, max=170),
        right_knee=AngleStats(mean=145, min=130, max=160),
        left_ankle=AngleStats(mean=90, min=82, max=100),
        right_ankle=AngleStats(mean=92, min=85, max=99),
    )
    assert k.left_knee.mean == 160


def test_timing_ms_total_field():
    t = TimingMs(frame_extract=420, mediapipe=1850, classify=12, feedback=1200, total=3500)
    assert t.total == 3500


def test_pose_class_literal():
    for c in ["GOOD_KICK", "BAD_KICK_KNEE_LOCKED", "GOOD_DRIBBLE", "BAD_DRIBBLE_OVERREACH"]:
        r = PoseAnalysisResponse(
            pose_class=c,
            class_name=c,
            confidence=0.9,
            class_probabilities={c: 0.9},
            key_angles=KeyAngles(
                left_knee=AngleStats(mean=160, min=150, max=170),
                right_knee=AngleStats(mean=145, min=130, max=160),
                left_ankle=AngleStats(mean=90, min=82, max=100),
                right_ankle=AngleStats(mean=92, min=85, max=99),
            ),
            feedback="ok",
            timing_ms=TimingMs(frame_extract=1, mediapipe=1, classify=1, feedback=1, total=4),
        )
        assert r.pose_class == c


def test_pose_class_invalid_rejected():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PoseAnalysisResponse(
            pose_class="WRONG",
            class_name="x",
            confidence=0.5,
            class_probabilities={},
            key_angles=KeyAngles(
                left_knee=AngleStats(mean=160, min=150, max=170),
                right_knee=AngleStats(mean=145, min=130, max=160),
                left_ankle=AngleStats(mean=90, min=82, max=100),
                right_ankle=AngleStats(mean=92, min=85, max=99),
            ),
            feedback="x",
            timing_ms=TimingMs(frame_extract=1, mediapipe=1, classify=1, feedback=1, total=4),
        )
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_pose_schemas.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: schemas.py 구현**

`ai-service/pose/schemas.py`:
```python
from typing import Literal

from pydantic import BaseModel, Field

PoseClass = Literal[
    "GOOD_KICK", "BAD_KICK_KNEE_LOCKED", "GOOD_DRIBBLE", "BAD_DRIBBLE_OVERREACH"
]

CLASS_NAMES_KO: dict[str, str] = {
    "GOOD_KICK": "좋은 킥",
    "BAD_KICK_KNEE_LOCKED": "킥 — 무릎 잠김",
    "GOOD_DRIBBLE": "좋은 드리블",
    "BAD_DRIBBLE_OVERREACH": "드리블 — 과도 리치",
}


class AngleStats(BaseModel):
    mean: float
    min: float
    max: float


class KeyAngles(BaseModel):
    left_knee: AngleStats
    right_knee: AngleStats
    left_ankle: AngleStats
    right_ankle: AngleStats


class TimingMs(BaseModel):
    frame_extract: int
    mediapipe: int
    classify: int
    feedback: int
    total: int


class PoseAnalysisResponse(BaseModel):
    pose_class: PoseClass
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    class_probabilities: dict[str, float]
    key_angles: KeyAngles
    feedback: str
    timing_ms: TimingMs
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_pose_schemas.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/pose/schemas.py ai-service/tests/test_pose_schemas.py
git commit -m "feat(pose): Pydantic schemas (PoseClass, AngleStats, KeyAngles, TimingMs)"
git push origin main
```

---

## Task 2: PoseExtractor (OpenCV + MediaPipe)

**Files:**
- Create: `ai-service/pose/extractor.py`
- Create: `ai-service/tests/test_pose_extractor.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_pose_extractor.py`:
```python
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from pose.extractor import PoseExtractor


def _fake_frame(h=480, w=640):
    return np.zeros((h, w, 3), dtype=np.uint8)


def test_extractor_returns_one_landmark_set_per_frame():
    fake_landmark = MagicMock()
    fake_landmark.landmark = [MagicMock(x=0.5, y=0.5, z=0.0, visibility=0.9) for _ in range(33)]

    fake_pose = MagicMock()
    fake_pose.process.return_value = MagicMock(pose_landmarks=fake_landmark)

    with patch("pose.extractor.mp.solutions.pose.Pose", return_value=fake_pose):
        ext = PoseExtractor(sample_fps=10)
        frames = [_fake_frame() for _ in range(5)]
        result = ext.extract_from_frames(frames)

    assert len(result) == 5
    assert len(result[0]) == 33
    assert all(p["visibility"] >= 0 for p in result[0])


def test_extractor_skips_frames_with_no_landmarks():
    fake_pose = MagicMock()
    fake_pose.process.return_value = MagicMock(pose_landmarks=None)

    with patch("pose.extractor.mp.solutions.pose.Pose", return_value=fake_pose):
        ext = PoseExtractor(sample_fps=10)
        frames = [_fake_frame() for _ in range(3)]
        result = ext.extract_from_frames(frames)

    assert result == []


def test_extract_from_video_path_uses_cv2():
    fake_cap = MagicMock()
    fake_cap.isOpened.return_value = True
    fake_cap.get.side_effect = lambda x: {5: 30.0, 7: 60}.get(x, 0)  # CAP_PROP_FPS=5, FRAME_COUNT=7
    fake_cap.read.side_effect = [(True, _fake_frame()), (True, _fake_frame()), (False, None)]

    with patch("pose.extractor.cv2.VideoCapture", return_value=fake_cap):
        ext = PoseExtractor(sample_fps=10)
        frames = ext._sample_frames("dummy.mp4")
    assert len(frames) >= 1


def test_max_frames_cap():
    fake_pose = MagicMock()
    fake_pose.process.return_value = MagicMock(
        pose_landmarks=MagicMock(landmark=[MagicMock(x=0, y=0, z=0, visibility=1) for _ in range(33)])
    )
    with patch("pose.extractor.mp.solutions.pose.Pose", return_value=fake_pose):
        ext = PoseExtractor(sample_fps=10, max_frames=10)
        frames = [_fake_frame() for _ in range(50)]
        result = ext.extract_from_frames(frames)
    assert len(result) == 10
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_pose_extractor.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: extractor.py 구현**

`ai-service/pose/extractor.py`:
```python
from __future__ import annotations

import cv2
import mediapipe as mp


class PoseExtractor:
    """OpenCV로 영상 → 프레임 + MediaPipe Pose → 33점 좌표."""

    def __init__(self, sample_fps: int = 10, max_frames: int = 300):
        self.sample_fps = sample_fps
        self.max_frames = max_frames
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def _sample_frames(self, video_path: str) -> list:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        step = max(1, int(src_fps / max(self.sample_fps, 1)))
        frames: list = []
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % step == 0:
                frames.append(frame)
                if len(frames) >= self.max_frames:
                    break
            idx += 1
        cap.release()
        return frames

    def extract_from_frames(self, frames: list) -> list[list[dict]]:
        """각 프레임의 33점 좌표 리스트. 사람 없는 프레임은 스킵."""
        out: list[list[dict]] = []
        for f in frames[: self.max_frames]:
            rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            result = self._pose.process(rgb)
            if result.pose_landmarks is None:
                continue
            points = []
            for lm in result.pose_landmarks.landmark:
                points.append(
                    {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
                )
            out.append(points)
        return out

    def extract_from_video(self, video_path: str) -> list[list[dict]]:
        frames = self._sample_frames(video_path)
        return self.extract_from_frames(frames)
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_pose_extractor.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/pose/extractor.py ai-service/tests/test_pose_extractor.py
git commit -m "feat(pose): PoseExtractor — OpenCV 프레임 추출 + MediaPipe 33점"
git push origin main
```

---

## Task 3: FeatureBuilder (관절 각도 + 상대 위치)

**Files:**
- Create: `ai-service/pose/features.py`
- Create: `ai-service/tests/test_pose_features.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_pose_features.py`:
```python
import math

import pytest

from pose.features import FeatureBuilder


def _flat_landmarks(coords: dict[int, tuple[float, float]]) -> list[dict]:
    """idx → (x, y) 매핑을 33점 리스트로 변환."""
    pts = []
    for i in range(33):
        x, y = coords.get(i, (0.0, 0.0))
        pts.append({"x": x, "y": y, "z": 0.0, "visibility": 1.0})
    return pts


def test_angle_180_when_collinear():
    # MediaPipe 인덱스: 23(left hip), 25(left knee), 27(left ankle)
    coords = {23: (0.0, 0.0), 25: (0.0, 1.0), 27: (0.0, 2.0)}
    fb = FeatureBuilder()
    angle = fb._joint_angle(_flat_landmarks(coords), 23, 25, 27)
    assert 178.0 <= angle <= 180.0


def test_angle_90_when_right_angle():
    # 직각 배치
    coords = {23: (0.0, 0.0), 25: (1.0, 0.0), 27: (1.0, 1.0)}
    fb = FeatureBuilder()
    angle = fb._joint_angle(_flat_landmarks(coords), 23, 25, 27)
    assert 88.0 <= angle <= 92.0


def test_build_returns_fixed_length_vector():
    coords = {i: (i * 0.01, i * 0.02) for i in range(33)}
    fb = FeatureBuilder()
    vec = fb.build_single([_flat_landmarks(coords) for _ in range(5)])
    # 12 각도 × (mean + std) + N relative positions
    assert len(vec) == fb.feature_dim()
    assert all(isinstance(v, float) for v in vec)


def test_build_empty_raises():
    fb = FeatureBuilder()
    with pytest.raises(ValueError):
        fb.build_single([])


def test_feature_dim_is_constant():
    fb1 = FeatureBuilder()
    fb2 = FeatureBuilder()
    assert fb1.feature_dim() == fb2.feature_dim() > 0
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_pose_features.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: features.py 구현**

`ai-service/pose/features.py`:
```python
from __future__ import annotations

import math

import numpy as np

# MediaPipe Pose landmark indices
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_FOOT = 31
RIGHT_FOOT = 32
NOSE = 0

# 각도 12개 (a, b, c) — b를 꼭짓점으로
ANGLE_TRIPLES = [
    (LEFT_HIP, LEFT_KNEE, LEFT_ANKLE),       # 좌 무릎
    (RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE),    # 우 무릎
    (LEFT_KNEE, LEFT_ANKLE, LEFT_FOOT),      # 좌 발목
    (RIGHT_KNEE, RIGHT_ANKLE, RIGHT_FOOT),   # 우 발목
    (LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE),    # 좌 엉덩이
    (RIGHT_SHOULDER, RIGHT_HIP, RIGHT_KNEE), # 우 엉덩이
    (NOSE, LEFT_SHOULDER, LEFT_ELBOW),       # 좌 어깨
    (NOSE, RIGHT_SHOULDER, RIGHT_ELBOW),     # 우 어깨
    (LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST), # 좌 팔꿈치
    (RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST),  # 우 팔꿈치
    (LEFT_ELBOW, LEFT_WRIST, LEFT_HIP),      # 좌 손목
    (RIGHT_ELBOW, RIGHT_WRIST, RIGHT_HIP),   # 우 손목
]

# 상대 위치: 몸 중심(hip 중점) 기준 정규화 좌표 (x, y)
RELATIVE_POINTS = [LEFT_FOOT, RIGHT_FOOT, LEFT_WRIST, RIGHT_WRIST, NOSE]


class FeatureBuilder:
    """33점 좌표 시퀀스 → 고정 길이 feature 벡터."""

    def feature_dim(self) -> int:
        # 12 각도 × (mean + std) + 5 relative points × (x, y) × (mean + std)
        return len(ANGLE_TRIPLES) * 2 + len(RELATIVE_POINTS) * 2 * 2

    @staticmethod
    def _joint_angle(landmarks: list[dict], a: int, b: int, c: int) -> float:
        pa = np.array([landmarks[a]["x"], landmarks[a]["y"]])
        pb = np.array([landmarks[b]["x"], landmarks[b]["y"]])
        pc = np.array([landmarks[c]["x"], landmarks[c]["y"]])
        v1 = pa - pb
        v2 = pc - pb
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 < 1e-9 or n2 < 1e-9:
            return 180.0
        cos = float(np.dot(v1, v2) / (n1 * n2))
        cos = max(-1.0, min(1.0, cos))
        return math.degrees(math.acos(cos))

    @staticmethod
    def _normalized_position(landmarks: list[dict], idx: int) -> tuple[float, float]:
        hx = (landmarks[LEFT_HIP]["x"] + landmarks[RIGHT_HIP]["x"]) / 2.0
        hy = (landmarks[LEFT_HIP]["y"] + landmarks[RIGHT_HIP]["y"]) / 2.0
        return landmarks[idx]["x"] - hx, landmarks[idx]["y"] - hy

    def build_single(self, frame_landmarks: list[list[dict]]) -> list[float]:
        if not frame_landmarks:
            raise ValueError("frame_landmarks is empty")
        angles_per_frame: list[list[float]] = []
        positions_per_frame: list[list[float]] = []
        for lm in frame_landmarks:
            angles_per_frame.append(
                [self._joint_angle(lm, a, b, c) for (a, b, c) in ANGLE_TRIPLES]
            )
            positions_per_frame.append(
                [v for idx in RELATIVE_POINTS for v in self._normalized_position(lm, idx)]
            )
        angles = np.array(angles_per_frame)
        positions = np.array(positions_per_frame)
        vec: list[float] = []
        vec.extend(angles.mean(axis=0).tolist())
        vec.extend(angles.std(axis=0).tolist())
        vec.extend(positions.mean(axis=0).tolist())
        vec.extend(positions.std(axis=0).tolist())
        return [float(v) for v in vec]
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_pose_features.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/pose/features.py ai-service/tests/test_pose_features.py
git commit -m "feat(pose): FeatureBuilder — 관절 각도 12 + 상대 위치"
git push origin main
```

---

## Task 4: train.py + compare.py (RF/MLP 학습 + 비교)

**Files:**
- Create: `ai-service/pose/train.py`
- Create: `ai-service/pose/compare.py`

학습은 데이터 의존이라 자동 테스트는 어렵다. CLI 실행 결과로 검증.

- [ ] **Step 1: train.py 구현 (RF·MLP 둘 다 학습 + 우수 모델 저장)**

`ai-service/pose/train.py`:
```python
"""풋살 자세 4분류 모델 학습.

사용법:
    python -m pose.train --features data/pose_features.csv --out models/best.joblib
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


CLASSES = ["GOOD_KICK", "BAD_KICK_KNEE_LOCKED", "GOOD_DRIBBLE", "BAD_DRIBBLE_OVERREACH"]


class MLP(nn.Module):
    def __init__(self, in_dim: int, n_classes: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, n_classes),
        )

    def forward(self, x):
        return self.net(x)


def _train_rf(X_train, y_train):
    model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    return model


def _train_mlp(X_train, y_train, in_dim: int, n_classes: int, epochs: int = 60):
    Xt = torch.tensor(X_train, dtype=torch.float32)
    yt = torch.tensor(y_train, dtype=torch.long)
    model = MLP(in_dim, n_classes)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    for _ in range(epochs):
        opt.zero_grad()
        logits = model(Xt)
        loss = loss_fn(logits, yt)
        loss.backward()
        opt.step()
    return model


def _eval_rf(model, X_test, y_test):
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    f1 = f1_score(y_test, pred, average="macro")
    return {"accuracy": acc, "f1_macro": f1, "pred": pred}


def _eval_mlp(model, X_test, y_test):
    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor(X_test, dtype=torch.float32))
        pred = logits.argmax(dim=1).numpy()
    acc = accuracy_score(y_test, pred)
    f1 = f1_score(y_test, pred, average="macro")
    return {"accuracy": acc, "f1_macro": f1, "pred": pred}


def _measure_inference_time(model, X_test, kind: str) -> float:
    n = min(100, len(X_test))
    sample = X_test[:n]
    if kind == "rf":
        t0 = time.perf_counter()
        for x in sample:
            model.predict(x.reshape(1, -1))
        t1 = time.perf_counter()
    else:
        model.eval()
        Xt = torch.tensor(sample, dtype=torch.float32)
        t0 = time.perf_counter()
        with torch.no_grad():
            for i in range(n):
                model(Xt[i : i + 1])
        t1 = time.perf_counter()
    return (t1 - t0) / n * 1000.0  # ms per inference


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", default="data/pose_features.csv", type=Path)
    parser.add_argument("--out", default="models/best.joblib", type=Path)
    parser.add_argument(
        "--card", default="models/model_card.md", type=Path, help="모델 선정 근거 마크다운"
    )
    args = parser.parse_args()

    if not args.features.exists():
        raise SystemExit(
            f"feature CSV 없음: {args.features}\n"
            "AI Hub 데이터 → 영상 → MediaPipe → features.py로 추출 후 CSV 생성 필요"
        )

    df = pd.read_csv(args.features)
    label_col = "label"
    X = df.drop(columns=[label_col]).values
    le = LabelEncoder().fit(CLASSES)
    y = le.transform(df[label_col].values)

    scaler = StandardScaler().fit(X)
    X = scaler.transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("== RF 학습 ==")
    rf = _train_rf(X_train, y_train)
    rf_metrics = _eval_rf(rf, X_test, y_test)
    rf_ms = _measure_inference_time(rf, X_test, "rf")
    print(f"RF accuracy={rf_metrics['accuracy']:.3f} f1={rf_metrics['f1_macro']:.3f} {rf_ms:.2f} ms/inf")

    print("== MLP 학습 ==")
    mlp = _train_mlp(X_train, y_train, in_dim=X.shape[1], n_classes=len(CLASSES))
    mlp_metrics = _eval_mlp(mlp, X_test, y_test)
    mlp_ms = _measure_inference_time(mlp, X_test, "mlp")
    print(
        f"MLP accuracy={mlp_metrics['accuracy']:.3f} f1={mlp_metrics['f1_macro']:.3f} {mlp_ms:.2f} ms/inf"
    )

    # 우수 모델 선정: accuracy 우선, 동률이면 추론 빠른 쪽
    if rf_metrics["accuracy"] > mlp_metrics["accuracy"] or (
        rf_metrics["accuracy"] == mlp_metrics["accuracy"] and rf_ms <= mlp_ms
    ):
        winner, winner_name = rf, "RandomForest"
        metrics = rf_metrics
        inf_ms = rf_ms
    else:
        winner, winner_name = mlp, "MLP"
        metrics = mlp_metrics
        inf_ms = mlp_ms

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if winner_name == "RandomForest":
        joblib.dump({"model": winner, "scaler": scaler, "kind": "rf", "classes": CLASSES}, args.out)
    else:
        torch.save(winner.state_dict(), args.out.with_suffix(".pt"))
        joblib.dump(
            {"scaler": scaler, "kind": "mlp", "in_dim": X.shape[1], "classes": CLASSES},
            args.out,
        )

    card = (
        f"# Pose Classifier Model Card\n\n"
        f"- 학습 데이터: {args.features} (n={len(df)})\n"
        f"- 분할: 80% train / 20% test\n"
        f"- 선정 모델: **{winner_name}**\n"
        f"- 정확도: {metrics['accuracy']:.3f}\n"
        f"- F1 macro: {metrics['f1_macro']:.3f}\n"
        f"- 추론 시간 (per inference): {inf_ms:.2f} ms\n\n"
        f"## RF vs MLP 비교\n\n"
        f"| 모델 | accuracy | f1_macro | inference ms |\n"
        f"|---|---|---|---|\n"
        f"| RandomForest | {rf_metrics['accuracy']:.3f} | {rf_metrics['f1_macro']:.3f} | {rf_ms:.2f} |\n"
        f"| MLP | {mlp_metrics['accuracy']:.3f} | {mlp_metrics['f1_macro']:.3f} | {mlp_ms:.2f} |\n"
    )
    args.card.write_text(card, encoding="utf-8")
    print(f"저장: {args.out} ({winner_name}) + {args.card}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: compare.py 구현 (단순 wrapper)**

`ai-service/pose/compare.py`:
```python
"""train.py를 호출하여 RF/MLP 비교 리포트만 생성하는 thin wrapper.

사용법:
    python -m pose.compare
"""
from . import train

if __name__ == "__main__":
    train.main()
```

- [ ] **Step 3: 동작 검증 (AI Hub 데이터 도착 후)**

```powershell
cd ai-service
python -m pose.train --features data/pose_features.csv --out models/best.joblib
```
Expected: RF·MLP 두 줄 출력 + `models/best.joblib` 또는 `models/best.pt` 생성 + `models/model_card.md` 작성.

> 데이터 아직이면 일단 스킵, 본 Task의 commit만 진행. Day 4에 데이터 들어오면 실행.

- [ ] **Step 4: Commit**

```powershell
git add ai-service/pose/train.py ai-service/pose/compare.py
git commit -m "feat(pose): train.py + compare.py — RF/MLP 학습 + 우수 모델 저장"
git push origin main
```

---

## Task 5: PoseClassifier (서비스 모델 1개 로드 + 예측)

**Files:**
- Create: `ai-service/pose/classifier.py`
- Create: `ai-service/tests/test_pose_classifier.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_pose_classifier.py`:
```python
from unittest.mock import MagicMock, patch

import numpy as np

from pose.classifier import PoseClassifier


def test_predict_rf_returns_class_and_probabilities():
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([1])
    mock_model.predict_proba.return_value = np.array([[0.05, 0.87, 0.04, 0.04]])

    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = np.array([[0.0] * 10])

    bundle = {
        "model": mock_model,
        "scaler": mock_scaler,
        "kind": "rf",
        "classes": ["GOOD_KICK", "BAD_KICK_KNEE_LOCKED", "GOOD_DRIBBLE", "BAD_DRIBBLE_OVERREACH"],
    }
    with patch("pose.classifier.joblib.load", return_value=bundle):
        clf = PoseClassifier("fake.joblib")
        cls, conf, probs = clf.predict([0.0] * 10)

    assert cls == "BAD_KICK_KNEE_LOCKED"
    assert 0.85 <= conf <= 0.88
    assert probs["BAD_KICK_KNEE_LOCKED"] == 0.87


def test_predict_mlp_path_loads_state_dict(tmp_path):
    bundle = {
        "scaler": MagicMock(transform=MagicMock(return_value=np.zeros((1, 10)))),
        "kind": "mlp",
        "in_dim": 10,
        "classes": ["GOOD_KICK", "BAD_KICK_KNEE_LOCKED", "GOOD_DRIBBLE", "BAD_DRIBBLE_OVERREACH"],
    }
    fake_logits = MagicMock()
    fake_logits.numpy.return_value = np.array([0.1, 2.5, 0.0, 0.3])

    fake_model = MagicMock()
    fake_model.return_value = MagicMock(
        squeeze=MagicMock(return_value=MagicMock(numpy=lambda: np.array([0.1, 2.5, 0.0, 0.3])))
    )

    with patch("pose.classifier.joblib.load", return_value=bundle), patch(
        "pose.classifier.torch.load", return_value={}
    ), patch("pose.classifier.MLP", return_value=fake_model):
        clf = PoseClassifier("fake.joblib")
        cls, conf, probs = clf.predict([0.0] * 10)

    assert cls == "BAD_KICK_KNEE_LOCKED"
    assert sum(probs.values()) > 0.99
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_pose_classifier.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: classifier.py 구현**

`ai-service/pose/classifier.py`:
```python
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .train import MLP  # 모델 클래스 재사용


class PoseClassifier:
    """학습된 모델 1개 로드 + 단일 feature vector 예측."""

    def __init__(self, model_path: str | Path):
        bundle = joblib.load(model_path)
        self._scaler = bundle["scaler"]
        self._classes: list[str] = bundle["classes"]
        self._kind: str = bundle["kind"]

        if self._kind == "rf":
            self._model = bundle["model"]
        elif self._kind == "mlp":
            in_dim = bundle["in_dim"]
            self._model = MLP(in_dim, len(self._classes))
            pt_path = Path(model_path).with_suffix(".pt")
            self._model.load_state_dict(torch.load(pt_path, weights_only=True))
            self._model.eval()
        else:
            raise ValueError(f"unknown model kind: {self._kind}")

    def predict(self, feature_vec: list[float]) -> tuple[str, float, dict[str, float]]:
        X = self._scaler.transform(np.array(feature_vec).reshape(1, -1))
        if self._kind == "rf":
            probs = self._model.predict_proba(X)[0]
            idx = int(np.argmax(probs))
        else:
            with torch.no_grad():
                logits = self._model(torch.tensor(X, dtype=torch.float32))
                probs_t = F.softmax(logits.squeeze(0), dim=0)
            probs = probs_t.numpy()
            idx = int(np.argmax(probs))
        class_name = self._classes[idx]
        confidence = float(probs[idx])
        probabilities = {self._classes[i]: float(probs[i]) for i in range(len(self._classes))}
        return class_name, confidence, probabilities
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_pose_classifier.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/pose/classifier.py ai-service/tests/test_pose_classifier.py
git commit -m "feat(pose): PoseClassifier — 최종 모델 1개 로드 + 예측"
git push origin main
```

---

## Task 6: FeedbackGenerator (Claude 자연어 피드백)

**Files:**
- Create: `ai-service/pose/feedback.py`
- Create: `ai-service/tests/test_pose_feedback.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_pose_feedback.py`:
```python
from unittest.mock import MagicMock

from pose.feedback import FeedbackGenerator
from pose.schemas import AngleStats, KeyAngles


def _angles():
    return KeyAngles(
        left_knee=AngleStats(mean=168, min=158, max=175),
        right_knee=AngleStats(mean=145, min=130, max=160),
        left_ankle=AngleStats(mean=90, min=82, max=100),
        right_ankle=AngleStats(mean=92, min=85, max=99),
    )


def test_feedback_includes_class_and_angles_in_prompt():
    claude = MagicMock()
    claude.chat.return_value = "무릎이 너무 펴진 상태예요."

    gen = FeedbackGenerator(claude_client=claude)
    out = gen.generate(
        pose_class="BAD_KICK_KNEE_LOCKED",
        confidence=0.87,
        key_angles=_angles(),
    )

    assert "무릎이 너무 펴진" in out
    args, kwargs = claude.chat.call_args
    user = kwargs["user"]
    assert "BAD_KICK_KNEE_LOCKED" in user
    assert "168" in user or "168.0" in user
    assert "0.87" in user or "87" in user


def test_feedback_falls_back_on_claude_error():
    claude = MagicMock()
    claude.chat.side_effect = RuntimeError("api down")
    gen = FeedbackGenerator(claude_client=claude)
    out = gen.generate(pose_class="GOOD_KICK", confidence=0.95, key_angles=_angles())
    assert "분류 결과" in out  # 폴백 문구
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_pose_feedback.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: feedback.py 구현**

`ai-service/pose/feedback.py`:
```python
from __future__ import annotations

from rag.claude_client import ClaudeClient

from .schemas import KeyAngles

SYSTEM_PROMPT = (
    "당신은 풋살 코치입니다. 사용자의 자세 분류 결과와 핵심 관절 각도를 보고, "
    "2~4문장의 친근한 한국어 피드백을 작성하세요. "
    "구체적인 각도 수치를 한 번만 인용하고, 실천 가능한 개선 팁을 1가지 제시하세요. "
    "이모지·과장된 표현은 피하세요."
)


class FeedbackGenerator:
    def __init__(self, claude_client: ClaudeClient):
        self._claude = claude_client

    def generate(
        self, pose_class: str, confidence: float, key_angles: KeyAngles
    ) -> str:
        user = (
            f"분류 결과: {pose_class} (신뢰도 {confidence:.2f})\n\n"
            f"핵심 관절 각도(평균):\n"
            f"- 좌 무릎: {key_angles.left_knee.mean:.1f}도\n"
            f"- 우 무릎: {key_angles.right_knee.mean:.1f}도\n"
            f"- 좌 발목: {key_angles.left_ankle.mean:.1f}도\n"
            f"- 우 발목: {key_angles.right_ankle.mean:.1f}도\n\n"
            "이 결과에 대한 친근한 한국어 피드백을 작성해주세요."
        )
        try:
            return self._claude.chat(system=SYSTEM_PROMPT, user=user, max_tokens=300).strip()
        except Exception:
            return f"분류 결과는 {pose_class}입니다. 자세 분석을 다시 시도해 주세요."
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_pose_feedback.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/pose/feedback.py ai-service/tests/test_pose_feedback.py
git commit -m "feat(pose): FeedbackGenerator — Claude로 자연어 피드백 생성"
git push origin main
```

---

## Task 7: FastAPI `/pose/analyze` 엔드포인트

**Files:**
- Modify: `ai-service/main.py`
- Create: `ai-service/tests/test_pose_endpoint.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_pose_endpoint.py`:
```python
import importlib
import io
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_CHROMA_DIR", str(tmp_path / "no_such"))
    monkeypatch.setenv("POSE_MODEL_PATH", str(tmp_path / "no_such.joblib"))
    import main as _main

    importlib.reload(_main)

    from pose.schemas import AngleStats, KeyAngles

    fake_extractor = MagicMock()
    fake_extractor.extract_from_video.return_value = [[{"x": 0, "y": 0, "z": 0, "visibility": 1}] * 33] * 5
    fake_features = MagicMock()
    fake_features.build_single.return_value = [0.0] * 10
    fake_classifier = MagicMock()
    fake_classifier.predict.return_value = (
        "BAD_KICK_KNEE_LOCKED",
        0.87,
        {"GOOD_KICK": 0.05, "BAD_KICK_KNEE_LOCKED": 0.87, "GOOD_DRIBBLE": 0.04, "BAD_DRIBBLE_OVERREACH": 0.04},
    )
    fake_feedback = MagicMock()
    fake_feedback.generate.return_value = "무릎이 너무 펴졌어요."

    _main.pose_extractor = fake_extractor
    _main.pose_features = fake_features
    _main.pose_classifier = fake_classifier
    _main.pose_feedback = fake_feedback

    with TestClient(_main.app) as client:
        yield client


def test_pose_analyze_returns_response(test_client, tmp_path):
    fake_mp4 = io.BytesIO(b"fake mp4 bytes")
    resp = test_client.post(
        "/pose/analyze",
        files={"file": ("test.mp4", fake_mp4, "video/mp4")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pose_class"] == "BAD_KICK_KNEE_LOCKED"
    assert body["confidence"] == 0.87
    assert "key_angles" in body
    assert "timing_ms" in body
    assert "total" in body["timing_ms"]


def test_pose_analyze_requires_file(test_client):
    resp = test_client.post("/pose/analyze")
    assert resp.status_code == 422
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_pose_endpoint.py -v
```
Expected: FAIL — endpoint 없음.

- [ ] **Step 3: main.py 수정 (전역 + lifespan + 엔드포인트 추가)**

`ai-service/main.py`의 import 섹션에 추가:
```python
from pose.classifier import PoseClassifier
from pose.extractor import PoseExtractor
from pose.features import FeatureBuilder
from pose.feedback import FeedbackGenerator
from pose.schemas import AngleStats, KeyAngles, PoseAnalysisResponse, TimingMs
```

전역 추가:
```python
pose_extractor: PoseExtractor | None = None
pose_features: FeatureBuilder | None = None
pose_classifier: PoseClassifier | None = None
pose_feedback: FeedbackGenerator | None = None

POSE_MODEL_PATH = Path(os.environ.get("POSE_MODEL_PATH", "models/best.joblib"))
```

`lifespan` 함수에 (agent_graph 빌드 다음에) 추가:
```python
    global pose_extractor, pose_features, pose_classifier, pose_feedback
    pose_extractor = PoseExtractor(sample_fps=10, max_frames=300)
    pose_features = FeatureBuilder()
    if POSE_MODEL_PATH.exists() and rag_chain is not None:
        pose_classifier = PoseClassifier(POSE_MODEL_PATH)
        pose_feedback = FeedbackGenerator(claude_client=rag_chain._claude)
```

`/agent/run` 다음에 엔드포인트 추가:
```python
import tempfile
import time as _time

from fastapi import File, UploadFile


@app.post("/pose/analyze", response_model=PoseAnalysisResponse)
def pose_analyze(file: UploadFile = File(...)):
    if pose_classifier is None or pose_feedback is None:
        raise HTTPException(status_code=503, detail="Pose 모델이 로드되지 않았습니다.")

    t0 = _time.perf_counter()
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(file.file.read())
        tmp_path = f.name

    t_frame_start = _time.perf_counter()
    landmarks_per_frame = pose_extractor.extract_from_video(tmp_path)
    t_frame_end = _time.perf_counter()

    if not landmarks_per_frame:
        raise HTTPException(status_code=400, detail="영상에서 사람이 보이지 않아요.")

    feature_vec = pose_features.build_single(landmarks_per_frame)
    t_features_end = _time.perf_counter()

    pose_class, confidence, probs = pose_classifier.predict(feature_vec)
    t_classify_end = _time.perf_counter()

    key_angles = _key_angles_from_landmarks(landmarks_per_frame)

    t_feedback_start = _time.perf_counter()
    feedback = pose_feedback.generate(pose_class, confidence, key_angles)
    t_feedback_end = _time.perf_counter()

    from pose.schemas import CLASS_NAMES_KO

    return PoseAnalysisResponse(
        pose_class=pose_class,
        class_name=CLASS_NAMES_KO.get(pose_class, pose_class),
        confidence=confidence,
        class_probabilities=probs,
        key_angles=key_angles,
        feedback=feedback,
        timing_ms=TimingMs(
            frame_extract=int((t_frame_end - t_frame_start) * 1000),
            mediapipe=int((t_features_end - t_frame_end) * 1000),
            classify=int((t_classify_end - t_features_end) * 1000),
            feedback=int((t_feedback_end - t_feedback_start) * 1000),
            total=int((t_feedback_end - t0) * 1000),
        ),
    )


def _key_angles_from_landmarks(landmarks_per_frame):
    import numpy as np
    from pose.features import (
        LEFT_HIP, LEFT_KNEE, LEFT_ANKLE, LEFT_FOOT,
        RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE, RIGHT_FOOT,
        FeatureBuilder,
    )
    fb = FeatureBuilder()
    triples = {
        "left_knee": (LEFT_HIP, LEFT_KNEE, LEFT_ANKLE),
        "right_knee": (RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE),
        "left_ankle": (LEFT_KNEE, LEFT_ANKLE, LEFT_FOOT),
        "right_ankle": (RIGHT_KNEE, RIGHT_ANKLE, RIGHT_FOOT),
    }
    stats: dict[str, AngleStats] = {}
    for name, (a, b, c) in triples.items():
        vals = [fb._joint_angle(lm, a, b, c) for lm in landmarks_per_frame]
        arr = np.array(vals)
        stats[name] = AngleStats(mean=float(arr.mean()), min=float(arr.min()), max=float(arr.max()))
    return KeyAngles(**stats)
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_pose_endpoint.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/main.py ai-service/tests/test_pose_endpoint.py
git commit -m "feat(pose): FastAPI /pose/analyze 엔드포인트 + multipart 영상 처리"
git push origin main
```

---

## Task 8: Java DTO 3개

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/dto/PoseAnalysisDTO.java`
- Create: `src/main/java/io/github/wizwix/letsfutsal/dto/KeyAnglesDTO.java`
- Create: `src/main/java/io/github/wizwix/letsfutsal/dto/TimingMsDTO.java`

테스트 없음. 다음 Task의 PoseServiceTest에서 검증.

- [ ] **Step 1: TimingMsDTO**

```java
package io.github.wizwix.letsfutsal.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class TimingMsDTO {
  @JsonProperty("frame_extract")
  private int frameExtract;

  private int mediapipe;
  private int classify;
  private int feedback;
  private int total;

  public int getFrameExtract() { return frameExtract; }
  public void setFrameExtract(int v) { this.frameExtract = v; }
  public int getMediapipe() { return mediapipe; }
  public void setMediapipe(int v) { this.mediapipe = v; }
  public int getClassify() { return classify; }
  public void setClassify(int v) { this.classify = v; }
  public int getFeedback() { return feedback; }
  public void setFeedback(int v) { this.feedback = v; }
  public int getTotal() { return total; }
  public void setTotal(int v) { this.total = v; }
}
```

- [ ] **Step 2: KeyAnglesDTO (nested AngleStats)**

```java
package io.github.wizwix.letsfutsal.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class KeyAnglesDTO {
  public static class AngleStats {
    private double mean;
    private double min;
    private double max;
    public double getMean() { return mean; }
    public void setMean(double mean) { this.mean = mean; }
    public double getMin() { return min; }
    public void setMin(double min) { this.min = min; }
    public double getMax() { return max; }
    public void setMax(double max) { this.max = max; }
  }

  @JsonProperty("left_knee")
  private AngleStats leftKnee;

  @JsonProperty("right_knee")
  private AngleStats rightKnee;

  @JsonProperty("left_ankle")
  private AngleStats leftAnkle;

  @JsonProperty("right_ankle")
  private AngleStats rightAnkle;

  public AngleStats getLeftKnee() { return leftKnee; }
  public void setLeftKnee(AngleStats v) { this.leftKnee = v; }
  public AngleStats getRightKnee() { return rightKnee; }
  public void setRightKnee(AngleStats v) { this.rightKnee = v; }
  public AngleStats getLeftAnkle() { return leftAnkle; }
  public void setLeftAnkle(AngleStats v) { this.leftAnkle = v; }
  public AngleStats getRightAnkle() { return rightAnkle; }
  public void setRightAnkle(AngleStats v) { this.rightAnkle = v; }
}
```

- [ ] **Step 3: PoseAnalysisDTO**

```java
package io.github.wizwix.letsfutsal.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

public class PoseAnalysisDTO {
  @JsonProperty("pose_class")
  private String poseClass;

  @JsonProperty("class_name")
  private String className;

  private double confidence;

  @JsonProperty("class_probabilities")
  private Map<String, Double> classProbabilities;

  @JsonProperty("key_angles")
  private KeyAnglesDTO keyAngles;

  private String feedback;

  @JsonProperty("timing_ms")
  private TimingMsDTO timingMs;

  public String getPoseClass() { return poseClass; }
  public void setPoseClass(String v) { this.poseClass = v; }
  public String getClassName() { return className; }
  public void setClassName(String v) { this.className = v; }
  public double getConfidence() { return confidence; }
  public void setConfidence(double v) { this.confidence = v; }
  public Map<String, Double> getClassProbabilities() { return classProbabilities; }
  public void setClassProbabilities(Map<String, Double> v) { this.classProbabilities = v; }
  public KeyAnglesDTO getKeyAngles() { return keyAngles; }
  public void setKeyAngles(KeyAnglesDTO v) { this.keyAngles = v; }
  public String getFeedback() { return feedback; }
  public void setFeedback(String v) { this.feedback = v; }
  public TimingMsDTO getTimingMs() { return timingMs; }
  public void setTimingMs(TimingMsDTO v) { this.timingMs = v; }
}
```

- [ ] **Step 4: 컴파일 확인**

```powershell
& $mvn -q compile
```
Expected: BUILD SUCCESS.

- [ ] **Step 5: Commit**

```powershell
git add src/main/java/io/github/wizwix/letsfutsal/dto/TimingMsDTO.java `
        src/main/java/io/github/wizwix/letsfutsal/dto/KeyAnglesDTO.java `
        src/main/java/io/github/wizwix/letsfutsal/dto/PoseAnalysisDTO.java
git commit -m "feat(pose): Pose DTO 3종 (PoseAnalysisDTO, KeyAnglesDTO, TimingMsDTO)"
git push origin main
```

---

## Task 9: PoseService (Python multipart 호출)

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/ai/PoseService.java`
- Create: `src/test/java/io/github/wizwix/letsfutsal/ai/PoseServiceTest.java`

- [ ] **Step 1: 실패 테스트 작성**

```java
package io.github.wizwix.letsfutsal.ai;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.PoseAnalysisDTO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

class PoseServiceTest {

  private RestTemplate restTemplate;
  private MockRestServiceServer server;
  private PoseService service;

  @BeforeEach
  void setUp() {
    restTemplate = new RestTemplate();
    server = MockRestServiceServer.createServer(restTemplate);
    service = new PoseService(restTemplate, new ObjectMapper(), "http://fake:8000");
  }

  @Test
  void analyze_parsesResponse() throws Exception {
    String json =
        "{\"pose_class\":\"BAD_KICK_KNEE_LOCKED\",\"class_name\":\"킥 — 무릎 잠김\","
            + "\"confidence\":0.87,"
            + "\"class_probabilities\":{\"GOOD_KICK\":0.05,\"BAD_KICK_KNEE_LOCKED\":0.87,"
            + "\"GOOD_DRIBBLE\":0.04,\"BAD_DRIBBLE_OVERREACH\":0.04},"
            + "\"key_angles\":{"
            + "\"left_knee\":{\"mean\":168,\"min\":158,\"max\":175},"
            + "\"right_knee\":{\"mean\":145,\"min\":130,\"max\":160},"
            + "\"left_ankle\":{\"mean\":90,\"min\":82,\"max\":100},"
            + "\"right_ankle\":{\"mean\":92,\"min\":85,\"max\":99}},"
            + "\"feedback\":\"무릎이 너무 펴졌어요.\","
            + "\"timing_ms\":{\"frame_extract\":420,\"mediapipe\":1850,"
            + "\"classify\":12,\"feedback\":1200,\"total\":3500}}";
    server
        .expect(requestTo("http://fake:8000/pose/analyze"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

    MockMultipartFile mp = new MockMultipartFile("file", "test.mp4", "video/mp4", new byte[]{0, 1, 2});
    PoseAnalysisDTO dto = service.analyze(mp);

    assertThat(dto.getPoseClass()).isEqualTo("BAD_KICK_KNEE_LOCKED");
    assertThat(dto.getConfidence()).isEqualTo(0.87);
    assertThat(dto.getKeyAngles().getLeftKnee().getMean()).isEqualTo(168);
    assertThat(dto.getTimingMs().getTotal()).isEqualTo(3500);
  }
}
```

- [ ] **Step 2: 실패 확인**

```powershell
& $mvn -q "-Dtest=PoseServiceTest" test
```
Expected: 컴파일 에러 — PoseService 없음.

- [ ] **Step 3: PoseService 구현**

```java
package io.github.wizwix.letsfutsal.ai;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.PoseAnalysisDTO;
import java.io.IOException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

@Service
public class PoseService {
  private static final Logger log = LoggerFactory.getLogger(PoseService.class);

  private final RestTemplate restTemplate;
  private final ObjectMapper objectMapper;
  private final String aiBaseUrl;

  @Autowired
  public PoseService(RestTemplate restTemplate, ObjectMapper objectMapper) {
    this(
        restTemplate,
        objectMapper,
        System.getenv().getOrDefault("AI_SERVICE_URL", "http://localhost:8000"));
  }

  public PoseService(RestTemplate restTemplate, ObjectMapper objectMapper, String aiBaseUrl) {
    this.restTemplate = restTemplate;
    this.objectMapper = objectMapper;
    this.aiBaseUrl = aiBaseUrl;
  }

  public PoseAnalysisDTO analyze(MultipartFile video) {
    try {
      byte[] bytes = video.getBytes();
      ByteArrayResource resource =
          new ByteArrayResource(bytes) {
            @Override
            public String getFilename() {
              return video.getOriginalFilename();
            }
          };

      MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
      body.add("file", resource);

      HttpHeaders headers = new HttpHeaders();
      headers.setContentType(MediaType.MULTIPART_FORM_DATA);

      HttpEntity<MultiValueMap<String, Object>> req = new HttpEntity<>(body, headers);
      return restTemplate.postForObject(aiBaseUrl + "/pose/analyze", req, PoseAnalysisDTO.class);
    } catch (IOException e) {
      log.warn("Pose 분석 영상 읽기 실패: {}", e.getMessage());
      throw new RuntimeException("영상 파일을 읽을 수 없습니다.", e);
    } catch (Exception e) {
      log.warn("Pose 분석 호출 실패: {}", e.getMessage());
      throw new RuntimeException("자세 분석 서비스 호출 실패", e);
    }
  }
}
```

- [ ] **Step 4: 통과 확인**

```powershell
& $mvn -q "-Dtest=PoseServiceTest" test
```
Expected: 1 test passed.

- [ ] **Step 5: Commit**

```powershell
git add src/main/java/io/github/wizwix/letsfutsal/ai/PoseService.java `
        src/test/java/io/github/wizwix/letsfutsal/ai/PoseServiceTest.java
git commit -m "feat(pose): PoseService — Python /pose/analyze multipart 호출"
git push origin main
```

---

## Task 10: PoseController + MockMvc 테스트

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/ai/PoseController.java`
- Create: `src/test/java/io/github/wizwix/letsfutsal/ai/PoseControllerTest.java`

- [ ] **Step 1: PoseControllerTest 작성**

```java
package io.github.wizwix.letsfutsal.ai;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import io.github.wizwix.letsfutsal.dto.PoseAnalysisDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

class PoseControllerTest {

  private MockMvc mockMvc;
  private PoseService poseService;
  private MockHttpSession session;

  @BeforeEach
  void setUp() {
    poseService = mock(PoseService.class);
    mockMvc = MockMvcBuilders.standaloneSetup(new PoseController(poseService)).build();

    session = new MockHttpSession();
    UserDTO user = new UserDTO();
    user.setUserId(1L);
    session.setAttribute("loginUser", user);
  }

  @Test
  void analyze_returnsAnalysis() throws Exception {
    PoseAnalysisDTO dto = new PoseAnalysisDTO();
    dto.setPoseClass("GOOD_KICK");
    dto.setConfidence(0.9);
    when(poseService.analyze(any())).thenReturn(dto);

    MockMultipartFile mp = new MockMultipartFile("file", "x.mp4", "video/mp4", new byte[]{0, 1});

    mockMvc
        .perform(multipart("/ai/pose/analyze").file(mp).session(session))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.pose_class").value("GOOD_KICK"));
  }

  @Test
  void analyze_returns401WithoutLogin() throws Exception {
    MockMultipartFile mp = new MockMultipartFile("file", "x.mp4", "video/mp4", new byte[]{0, 1});
    mockMvc
        .perform(multipart("/ai/pose/analyze").file(mp))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void posePage_returns200() throws Exception {
    mockMvc.perform(get("/ai/pose").session(session)).andExpect(status().isOk());
  }
}
```

- [ ] **Step 2: 실패 확인**

```powershell
& $mvn -q "-Dtest=PoseControllerTest" test
```
Expected: 컴파일 에러 — Controller 없음.

- [ ] **Step 3: PoseController 구현**

```java
package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.PoseAnalysisDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import jakarta.servlet.http.HttpSession;
import java.time.LocalDate;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.multipart.MultipartFile;

@Controller
@RequestMapping("/ai")
public class PoseController {

  private static final int DAILY_LIMIT = 10;
  private static final String COUNT_KEY = "poseAnalyzeCount";
  private static final String DATE_KEY = "poseAnalyzeDate";

  private final PoseService poseService;

  public PoseController(PoseService poseService) {
    this.poseService = poseService;
  }

  @GetMapping("/pose")
  public String page() {
    return "ai/pose";
  }

  @PostMapping("/pose/analyze")
  @ResponseBody
  public ResponseEntity<?> analyze(
      @RequestParam("file") MultipartFile file, HttpSession session) {
    UserDTO user = (UserDTO) session.getAttribute("loginUser");
    if (user == null) {
      return ResponseEntity.status(401).body(Map.of("error", "로그인이 필요해요."));
    }
    if (file.isEmpty()) {
      return ResponseEntity.badRequest().body(Map.of("error", "영상을 업로드해 주세요."));
    }
    if (file.getSize() > 50 * 1024 * 1024) {
      return ResponseEntity.badRequest().body(Map.of("error", "영상은 최대 50MB까지 가능해요."));
    }
    if (isRateLimited(session)) {
      return ResponseEntity.status(429).body(Map.of("error", "오늘 사용 한도(10회)에 도달했어요."));
    }
    PoseAnalysisDTO dto = poseService.analyze(file);
    incrementCount(session);
    return ResponseEntity.ok(dto);
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

- [ ] **Step 4: 통과 확인**

```powershell
& $mvn -q "-Dtest=PoseControllerTest" test
```
Expected: 3 tests passed.

- [ ] **Step 5: Commit**

```powershell
git add src/main/java/io/github/wizwix/letsfutsal/ai/PoseController.java `
        src/test/java/io/github/wizwix/letsfutsal/ai/PoseControllerTest.java
git commit -m "feat(pose): PoseController — /ai/pose 페이지 + multipart 분석 API"
git push origin main
```

---

## Task 11: /ai/pose JSP + JS + 네비 메뉴

**Files:**
- Create: `src/main/webapp/WEB-INF/views/ai/pose.jsp`
- Create: `src/main/webapp/resources/script/pose_analyzer.js`
- Modify: `src/main/webapp/WEB-INF/views/common/header.jsp`

- [ ] **Step 1: pose.jsp 작성**

`src/main/webapp/WEB-INF/views/ai/pose.jsp`:
```jsp
<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib uri="jakarta.tags.core" prefix="c" %>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>AI 자세 분석 — letsfutsal</title>
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/style/bootstrap/bootstrap.min.css">
  <style>
    :root { --accent: #00d4a3; --bg-1: #0a0a0a; --bg-3: #1a1a1a; --bg-4: #232323;
            --border: rgba(255,255,255,0.08); --text: #f5f5f5; --text-muted: #a0a0a0; }
    body { background: var(--bg-1); color: var(--text); }
    .pose-wrap { max-width: 880px; margin: 32px auto; padding: 0 24px; }
    .pose-card { background: linear-gradient(135deg, var(--bg-3), var(--bg-4));
                  border: 1px solid var(--border); border-radius: 16px; padding: 24px; }
    .upload-zone { border: 2px dashed var(--border); border-radius: 12px; padding: 32px;
                    text-align: center; cursor: pointer; transition: border-color 0.2s; }
    .upload-zone:hover, .upload-zone.dragging { border-color: var(--accent); }
    .btn-coord { padding: 12px 24px; border-radius: 12px; border: none; font-weight: 600;
                  cursor: pointer; background: linear-gradient(135deg, var(--accent), #00a37e);
                  color: #000; margin-top: 16px; }
    .result-card { background: var(--bg-3); border: 1px solid var(--border);
                    border-radius: 14px; padding: 20px; margin-top: 16px; }
    .angle-row { display: flex; justify-content: space-between; padding: 6px 0;
                  border-bottom: 1px dashed var(--border); }
    .badge-class { display: inline-block; padding: 6px 14px; border-radius: 8px;
                    background: rgba(0,212,163,0.15); color: var(--accent); font-weight: 700; }
    .feedback-box { background: rgba(0,212,163,0.05); border-left: 3px solid var(--accent);
                    padding: 14px; border-radius: 6px; margin-top: 12px; }
  </style>
</head>
<body>
<jsp:include page="/WEB-INF/views/common/header.jsp">
  <jsp:param name="menu" value="pose"/>
</jsp:include>

<section class="pose-wrap">
  <h1 style="background: linear-gradient(135deg, var(--accent), #6cf);
              -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
    🏃 AI 자세 분석
  </h1>
  <p style="color: var(--text-muted)">
    풋살 킥/드리블 영상을 업로드하면 AI가 자세를 분석해 드려요.<br>
    MediaPipe로 33개 관절을 추출하고 학습된 모델이 4가지 자세로 분류합니다.
  </p>

  <div class="pose-card">
    <div id="uploadZone" class="upload-zone">
      <div style="font-size:42px;">📹</div>
      <p>여기에 mp4 영상을 드롭하거나 클릭하여 선택<br>
        <small style="color:var(--text-muted)">최대 50MB · 30초 이내 권장</small></p>
      <input type="file" id="fileInput" accept="video/mp4,video/quicktime" style="display:none">
    </div>
    <div id="fileName" style="margin-top:12px; color:var(--text-muted)"></div>
    <button id="analyzeBtn" class="btn-coord" disabled>✨ 자세 분석 시작</button>
  </div>

  <div id="resultArea" style="display:none"></div>
</section>

<script>window.POSE_CTX = '${pageContext.request.contextPath}';</script>
<script src="${pageContext.request.contextPath}/resources/script/pose_analyzer.js"></script>
</body>
</html>
```

- [ ] **Step 2: pose_analyzer.js 작성**

`src/main/webapp/resources/script/pose_analyzer.js`:
```javascript
(function () {
  const ctx = window.POSE_CTX || '';
  const fileInput = document.getElementById('fileInput');
  const uploadZone = document.getElementById('uploadZone');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const fileNameEl = document.getElementById('fileName');
  const resultArea = document.getElementById('resultArea');
  let selectedFile = null;

  uploadZone.addEventListener('click', () => fileInput.click());
  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragging');
  });
  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragging'));
  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragging');
    if (e.dataTransfer.files.length) setFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) setFile(e.target.files[0]);
  });

  function setFile(f) {
    if (!f.type.startsWith('video/')) {
      alert('영상 파일만 업로드 가능해요.');
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      alert('영상은 최대 50MB까지 가능해요.');
      return;
    }
    selectedFile = f;
    fileNameEl.textContent = '선택됨: ' + f.name + ' (' + (f.size / 1024 / 1024).toFixed(1) + 'MB)';
    analyzeBtn.disabled = false;
  }

  analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '🔍 분석 중... (영상 길이에 따라 5~30초 소요)';
    resultArea.style.display = 'none';

    try {
      const form = new FormData();
      form.append('file', selectedFile);
      const resp = await fetch(ctx + '/ai/pose/analyze', { method: 'POST', body: form });
      if (resp.status === 401) {
        alert('로그인이 필요해요.');
        window.location.href = ctx + '/user/login';
        return;
      }
      const data = await resp.json();
      if (!resp.ok) {
        alert(data.error || '분석에 실패했어요.');
        return;
      }
      renderResult(data);
    } catch (e) {
      alert('네트워크 오류: ' + e.message);
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = '✨ 자세 분석 시작';
    }
  });

  function renderResult(d) {
    const ka = d.key_angles;
    const tm = d.timing_ms;
    resultArea.style.display = 'block';
    resultArea.innerHTML =
      '<div class="result-card">' +
      '<div style="margin-bottom:12px"><span class="badge-class">' + escapeHtml(d.class_name) + '</span> ' +
      '<small style="color:var(--text-muted);margin-left:8px">신뢰도 ' + (d.confidence * 100).toFixed(1) + '%</small></div>' +
      '<h3 style="font-size:16px;margin-top:16px">🦵 핵심 관절 각도 (평균)</h3>' +
      angleRow('좌 무릎', ka.left_knee) +
      angleRow('우 무릎', ka.right_knee) +
      angleRow('좌 발목', ka.left_ankle) +
      angleRow('우 발목', ka.right_ankle) +
      '<div class="feedback-box"><strong>💬 코치 피드백</strong><br>' + escapeHtml(d.feedback) + '</div>' +
      '<div style="margin-top:16px;color:var(--text-muted);font-size:12px">⏱️ 전체 처리: ' + tm.total + 'ms ' +
      '(프레임 ' + tm.frame_extract + ' / MediaPipe ' + tm.mediapipe + ' / 분류 ' + tm.classify + ' / 피드백 ' + tm.feedback + ')</div>' +
      '</div>';
  }

  function angleRow(label, a) {
    return '<div class="angle-row"><span>' + label + '</span>' +
      '<span>평균 <strong>' + a.mean.toFixed(1) + '°</strong> ' +
      '<small style="color:var(--text-muted)">(min ' + a.min.toFixed(0) + ' ~ max ' + a.max.toFixed(0) + ')</small></span></div>';
  }

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
})();
```

- [ ] **Step 3: 네비 메뉴 추가**

`src/main/webapp/WEB-INF/views/common/header.jsp`의 AI 코디네이터 메뉴 다음에 추가 (`<c:if>` 안):
```jsp
        <li class="nav-item">
          <a class="nav-link ${param.menu == 'pose' ? 'active' : ''}" href="${pageContext.request.contextPath}/ai/pose">🏃 자세 분석</a>
        </li>
```

- [ ] **Step 4: 빌드 + 수동 검증**

```powershell
& $mvn -q package "-DskipTests"
```
Expected: BUILD SUCCESS. Tomcat 재배포 후 `/ai/pose` 접속 → 페이지 정상 표시, 영상 업로드 가능.

- [ ] **Step 5: Commit**

```powershell
git add src/main/webapp/WEB-INF/views/ai/pose.jsp `
        src/main/webapp/resources/script/pose_analyzer.js `
        src/main/webapp/WEB-INF/views/common/header.jsp
git commit -m "feat(pose): /ai/pose JSP + 업로드 UI + 결과 시각화 + 네비 메뉴"
git push origin main
```

---

## Task 12: 평가 시스템 (eval/run_pose_eval.py)

**Files:**
- Create: `ai-service/eval/run_pose_eval.py`
- Create: `ai-service/eval/pose_test_videos/` (디렉토리, gitignore)

- [ ] **Step 1: eval/run_pose_eval.py 작성**

`ai-service/eval/run_pose_eval.py`:
```python
"""Pose 분석기 end-to-end 평가.

사용법:
    python -m eval.run_pose_eval

테스트 영상 디렉토리 구조:
    eval/pose_test_videos/
        GOOD_KICK_01.mp4
        BAD_KICK_KNEE_LOCKED_02.mp4
        ...
파일명 prefix가 라벨.
"""
from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from pose.classifier import PoseClassifier
from pose.extractor import PoseExtractor
from pose.features import FeatureBuilder
from pose.feedback import FeedbackGenerator
from rag.claude_client import ClaudeClient


def _label_from_filename(p: Path) -> str:
    for cls in ["GOOD_KICK", "BAD_KICK_KNEE_LOCKED", "GOOD_DRIBBLE", "BAD_DRIBBLE_OVERREACH"]:
        if p.stem.startswith(cls):
            return cls
    return "UNKNOWN"


def evaluate(videos_dir: Path, model_path: Path):
    videos = sorted(videos_dir.glob("*.mp4"))
    if not videos:
        raise SystemExit(f"테스트 영상 없음: {videos_dir}")

    extractor = PoseExtractor(sample_fps=10, max_frames=300)
    features = FeatureBuilder()
    classifier = PoseClassifier(model_path)
    feedback_gen = FeedbackGenerator(claude_client=ClaudeClient())

    correct = 0
    latencies: list[int] = []
    mp_latencies: list[int] = []
    feedback_latencies: list[int] = []
    results: list[dict] = []

    for v in videos:
        expected = _label_from_filename(v)
        t0 = time.perf_counter()
        landmarks = extractor.extract_from_video(str(v))
        t1 = time.perf_counter()
        if not landmarks:
            results.append({"video": v.name, "expected": expected, "predicted": None, "ok": False})
            continue
        vec = features.build_single(landmarks)
        pred, conf, probs = classifier.predict(vec)
        t2 = time.perf_counter()
        from main import _key_angles_from_landmarks  # 재사용

        ka = _key_angles_from_landmarks(landmarks)
        fb_text = feedback_gen.generate(pred, conf, ka)
        t3 = time.perf_counter()
        ok = pred == expected
        if ok:
            correct += 1
        latencies.append(int((t3 - t0) * 1000))
        mp_latencies.append(int((t1 - t0) * 1000))
        feedback_latencies.append(int((t3 - t2) * 1000))
        results.append(
            {
                "video": v.name,
                "expected": expected,
                "predicted": pred,
                "confidence": round(conf, 3),
                "ok": ok,
                "total_ms": int((t3 - t0) * 1000),
                "feedback_preview": fb_text[:80],
            }
        )

    n = max(1, len(videos))
    return {
        "service_accuracy": correct / n,
        "avg_total_ms": int(sum(latencies) / max(1, len(latencies))),
        "avg_mediapipe_ms": int(sum(mp_latencies) / max(1, len(mp_latencies))),
        "avg_feedback_ms": int(sum(feedback_latencies) / max(1, len(feedback_latencies))),
        "n": len(videos),
        "results": results,
    }


def format_report(metrics: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Pose 분석기 평가 리포트",
        "",
        f"- 실행: {now}  · 영상 수: {metrics['n']}",
        "",
        "## 지표",
        "",
        "| 지표 | 값 | 목표 | 통과 |",
        "|---|---|---|---|",
        f"| service_accuracy | {metrics['service_accuracy']:.3f} | ≥ 0.75 | "
        f"{'✅' if metrics['service_accuracy'] >= 0.75 else '❌'} |",
        f"| avg_total_ms | {metrics['avg_total_ms']} | ≤ 5000 | "
        f"{'✅' if metrics['avg_total_ms'] <= 5000 else '❌'} |",
        f"| avg_mediapipe_ms | {metrics['avg_mediapipe_ms']} | ≤ 3000 | "
        f"{'✅' if metrics['avg_mediapipe_ms'] <= 3000 else '❌'} |",
        f"| avg_feedback_ms | {metrics['avg_feedback_ms']} | ≤ 2000 | "
        f"{'✅' if metrics['avg_feedback_ms'] <= 2000 else '❌'} |",
        "",
        "## 영상별 결과",
        "",
        "| 파일 | expected | predicted | OK | total ms |",
        "|---|---|---|---|---|",
    ]
    for r in metrics["results"]:
        ok = '✅' if r.get("ok") else '❌'
        lines.append(
            f"| {r['video']} | {r['expected']} | {r.get('predicted', '-')} | {ok} | {r.get('total_ms', '-')} |"
        )
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--videos", default="eval/pose_test_videos", type=Path)
    p.add_argument("--model", default="models/best.joblib", type=Path)
    p.add_argument("--out", default=None, type=Path)
    args = p.parse_args()
    if args.out is None:
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        args.out = Path(f"eval/pose_report_{stamp}.md")
    metrics = evaluate(args.videos, args.model)
    report = format_report(metrics)
    args.out.write_text(report, encoding="utf-8")
    print(f"service_accuracy={metrics['service_accuracy']:.3f} avg_total={metrics['avg_total_ms']}ms")
    print(f"리포트: {args.out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 테스트 영상 디렉토리 생성**

```powershell
New-Item -ItemType Directory -Force ai-service/eval/pose_test_videos | Out-Null
```

테스트 영상 10~20개를 본인이 촬영하거나 AI Hub 일부를 라벨링 prefix로 복사. 데이터 들어오기 전엔 실행 보류.

- [ ] **Step 3: 실행 검증 (모델·영상 준비 후)**

```powershell
cd ai-service
python -m eval.run_pose_eval
```
Expected: 4 지표 출력 + `eval/pose_report_<timestamp>.md` 생성.

- [ ] **Step 4: Commit**

```powershell
git add ai-service/eval/run_pose_eval.py
git commit -m "feat(pose): run_pose_eval — service 정확도·latency 4지표 측정"
git push origin main
```

---

## Task 13: Task 15 통합 수동 smoke test

코드 작업 없음. Tomcat + Python 동시 실행 후 브라우저 데모.

- [ ] **Step 1: Python 서버 실행**

```powershell
cd ai-service
.\venv\Scripts\Activate.ps1
uvicorn main:app --port 8000
```

- [ ] **Step 2: Tomcat 재배포**

IntelliJ에서 Rebuild + Tomcat 재시작.

- [ ] **Step 3: 4 시나리오 브라우저 확인**

`http://localhost:8080/letsfutsal/ai/pose`:
1. 본인 인사이드 킥 영상 업로드 → `GOOD_KICK` + 자연어 피드백 + 각도 4개
2. 일부러 무릎 펴고 찬 영상 → `BAD_KICK_KNEE_LOCKED`
3. 드리블 영상 → `GOOD_DRIBBLE`
4. 사람 없는 영상 → 400 에러 + 친절 메시지

각 시나리오 스크린샷 캡처 (PR/이력서 첨부).

- [ ] **Step 4: 메모리 갱신**

`C:\Users\emdak\.claude\projects\C--letsfutsal\memory\`에 신규:
`project_pose_progress.md` — 진행 상태 + 평가 결과 + 향후 개선 항목.

---

## Task 14: 문서 + 로드맵 완료 표시

**Files:**
- Modify: `ai-service/README.md`
- Modify: `CLAUDE.md`
- Modify: `docs/ai-features-roadmap.md`

- [ ] **Step 1: ai-service/README.md에 Pose 섹션**

"## 구성 요소" 아래에 추가:
```markdown
- **ML 자세 분석** (`pose/`) — MediaPipe + scikit-learn/PyTorch + Claude 피드백 결합
```

엔드포인트 표에 추가:
```markdown
| POST | `/pose/analyze` | 영상 → 자세 분류 + 각도 + 자연어 피드백 |
```

신규 섹션:
```markdown
## Pose 모델 학습

\`\`\`powershell
python -m pose.train --features data/pose_features.csv --out models/best.joblib
\`\`\`

RF/MLP 둘 다 학습 후 더 우수한 모델 1개를 `models/best.joblib` (또는 `best.pt`)로 저장.
모델 선정 근거는 `models/model_card.md`.

## Pose 평가

\`\`\`powershell
python -m eval.run_pose_eval
\`\`\`

4지표: service_accuracy, avg_total_ms, avg_mediapipe_ms, avg_feedback_ms.
산출물: `eval/pose_report_<timestamp>.md`.
```

- [ ] **Step 2: CLAUDE.md "AI 기능 구조"에 Pose 항목 추가**

```markdown
**ML 풋살 자세 분석기** (`/ai/pose` 페이지)

별도 페이지에서 영상 업로드 → MediaPipe 33점 → feature engineering → 분류 모델 1개 → Claude 자연어 피드백.

- Spring: `ai/PoseController.java`, `ai/PoseService.java`, `dto/PoseAnalysisDTO.java`, `dto/KeyAnglesDTO.java`, `dto/TimingMsDTO.java`
- Python (`ai-service/pose/`): MediaPipe Pose + scikit-learn/PyTorch + Claude. 자세한 학습·평가는 [`ai-service/README.md`](ai-service/README.md).
- 환경: `POSE_MODEL_PATH` (기본 `models/best.joblib`)
- 레이트 리미트: 일일 10회
```

- [ ] **Step 3: docs/ai-features-roadmap.md "기능 1" 섹션 완료 표시**

기능 1 헤더를 `## 기능 1. 풋살 킥·드리블 자세 분석기 (ML / 이미지) ✅ 구현 완료 (YYYY-MM-DD)`로 변경 후 다음 추가:

```markdown
### 구현 결과
- AI Hub 스포츠 자세 영상 데이터셋으로 학습
- MediaPipe 33점 + 관절 각도 12 + 상대 위치 feature engineering
- RandomForest vs PyTorch MLP 비교 후 우수 모델 1개 서비스 배포 (`models/model_card.md`)
- /ai/pose 페이지: 영상 업로드 → 4분류 + 각도 차트 + Claude 자연어 피드백
- 평가 4지표 통과: service_accuracy, avg_total_ms, mediapipe_ms, feedback_ms

### 산출물
- Python `pose/` 6모듈 + `eval/run_pose_eval.py`
- Java PoseController/PoseService + DTO 3종
- JSP /ai/pose + pose_analyzer.js
- Pose 테스트 ~15개 (Python) + 4개 (Java) 통과
```

"다음 단계"에서 3번에 완료 표시:
```markdown
3. ~~**브레인스토밍 #3**: 기능 1 (ML 포즈 분석)~~ ✅ YYYY-MM-DD 구현 완료
```

- [ ] **Step 4: 빌드 + 전체 테스트 확인**

```powershell
cd ai-service; pytest -v
```
Expected: 모든 Python 테스트 그린.

```powershell
& $mvn -q test
```
Expected: 모든 Java 테스트 그린.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/README.md CLAUDE.md docs/ai-features-roadmap.md
git commit -m "docs: ML 풋살 자세 분석기 구현 완료 반영 (README, CLAUDE.md, 로드맵)"
git push origin main
```

---

## 최종 점검 체크리스트

- [ ] Python 모든 테스트 그린 (`pytest -v`)
- [ ] Java 모든 테스트 그린 (`mvn test`)
- [ ] WAR 빌드 성공
- [ ] 모델 비교 리포트 (`models/model_card.md`) 작성됨
- [ ] 서비스 평가 리포트 (`eval/pose_report_<ts>.md`) 작성됨
- [ ] 데모 시나리오 4개 캡처 (PR/이력서 첨부)
- [ ] 모든 commit이 origin/main에 push됨
- [ ] 메모리 진행 상태 갱신

---

## 위험 및 대응

| 위험 | 대응 |
|---|---|
| AI Hub 승인 1~2일 지연 | 그동안 Task 0~3 (mediapipe 셋업, schemas, extractor, features) 진행 |
| AI Hub 데이터에 풋살 동작 부족 | 본인 촬영 보충 (라벨 prefix 파일명) |
| MediaPipe Windows 호환 이슈 | mediapipe 0.10.x 최신 / Python 3.10~3.12 |
| RF·MLP 둘 다 정확도 < 0.75 | feature 차원 늘리기 (각도 24개로 확장), 또는 데이터 추가 수집 |
| MediaPipe latency > 3000ms | `model_complexity=0` 으로 낮춤 (정확도↓ 속도↑) |
| Tomcat URI 인코딩 (기능 3에서 이미 해결) | AgentDataController fix 패턴 재활용 |

---

## 다음 단계 (이 plan 완료 후)

- LangGraph 고도화 백로그 (tool_calls 캡처 등) 진행
- RAG faithfulness 0.556 개선
- 또는 7개 기술 모두 커버 완료 → 이력서·포트폴리오 마무리
