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

    fake_extractor = MagicMock()
    fake_extractor.extract_from_video.return_value = [
        [{"x": 0, "y": 0, "z": 0, "visibility": 1}] * 33 for _ in range(5)
    ]
    fake_features = MagicMock()
    fake_features.build_single.return_value = [0.0] * 10
    fake_classifier = MagicMock()
    fake_classifier.predict.return_value = (
        "INSTEP_KICK",
        0.87,
        {
            "INSIDE_KICK": 0.05,
            "INSTEP_KICK": 0.87,
            "INFRONT_KICK": 0.08,
        },
    )
    fake_feedback = MagicMock()
    fake_feedback.generate.return_value = "인스텝킥 자세가 안정적이에요."

    _main.pose_extractor = fake_extractor
    _main.pose_features = fake_features
    _main.pose_classifier = fake_classifier
    _main.pose_feedback = fake_feedback

    with TestClient(_main.app) as client:
        yield client


def test_pose_analyze_returns_response(test_client):
    fake_mp4 = io.BytesIO(b"fake mp4 bytes")
    resp = test_client.post(
        "/pose/analyze",
        files={"file": ("test.mp4", fake_mp4, "video/mp4")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pose_class"] == "INSTEP_KICK"
    assert body["confidence"] == 0.87
    assert "key_angles" in body
    assert "timing_ms" in body
    assert "total" in body["timing_ms"]


def test_pose_analyze_requires_file(test_client):
    resp = test_client.post("/pose/analyze")
    assert resp.status_code == 422
