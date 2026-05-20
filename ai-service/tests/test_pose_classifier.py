from unittest.mock import MagicMock, patch

import numpy as np

from pose.classifier import PoseClassifier


def test_predict_rf_returns_class_and_probabilities():
    mock_model = MagicMock()
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


def test_predict_mlp_path_uses_softmax():
    bundle = {
        "scaler": MagicMock(transform=MagicMock(return_value=np.zeros((1, 10)))),
        "kind": "mlp",
        "in_dim": 10,
        "classes": ["GOOD_KICK", "BAD_KICK_KNEE_LOCKED", "GOOD_DRIBBLE", "BAD_DRIBBLE_OVERREACH"],
    }

    import torch

    fake_logits = torch.tensor([[0.1, 2.5, 0.0, 0.3]])
    fake_model = MagicMock(return_value=fake_logits)
    fake_model.eval = MagicMock()

    with patch("pose.classifier.joblib.load", return_value=bundle), patch(
        "pose.classifier.torch.load", return_value={}
    ), patch("pose.classifier.MLP", return_value=fake_model):
        clf = PoseClassifier("fake.joblib")
        cls, conf, probs = clf.predict([0.0] * 10)

    assert cls == "BAD_KICK_KNEE_LOCKED"
    assert abs(sum(probs.values()) - 1.0) < 1e-3
