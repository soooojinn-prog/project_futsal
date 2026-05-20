from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import torch
import torch.nn.functional as F

from .train import MLP


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
        else:
            with torch.no_grad():
                logits = self._model(torch.tensor(X, dtype=torch.float32))
                probs_t = F.softmax(logits.squeeze(0), dim=0)
            probs = probs_t.numpy()
        idx = int(np.argmax(probs))
        class_name = self._classes[idx]
        confidence = float(probs[idx])
        probabilities = {
            self._classes[i]: float(probs[i]) for i in range(len(self._classes))
        }
        return class_name, confidence, probabilities
