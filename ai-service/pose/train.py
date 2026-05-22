"""풋살 킥 3분류 모델 학습.

사용법:
    python -m pose.train --features data/pose_features.csv --out models/best.joblib

CSV 형식: feature 컬럼 + 마지막 컬럼 `label` (INSIDE_KICK/INSTEP_KICK/INFRONT_KICK 중 하나).

* 드리블·패스 분류는 향후 Phase 2에서 추가 데이터 확보 후 확장 예정 (현재 비활성).
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


# Phase 1 — AI Hub 데이터 일부 다운로드 실패로 인프런트·남성 데이터 부재.
# 일단 여성 데이터 기준 2-class 학습. INFRONT_KICK는 Phase 2에 추가 학습 예정.
CLASSES = ["INSIDE_KICK", "INSTEP_KICK"]


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


def _eval_sklearn(model, X_test, y_test):
    pred = model.predict(X_test)
    return {
        "accuracy": accuracy_score(y_test, pred),
        "f1_macro": f1_score(y_test, pred, average="macro"),
    }


def _eval_mlp(model, X_test, y_test):
    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor(X_test, dtype=torch.float32))
        pred = logits.argmax(dim=1).numpy()
    return {
        "accuracy": accuracy_score(y_test, pred),
        "f1_macro": f1_score(y_test, pred, average="macro"),
    }


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
    return (t1 - t0) / max(n, 1) * 1000.0  # ms per inference


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", default="data/pose_features.csv", type=Path)
    parser.add_argument("--out", default="models/best.joblib", type=Path)
    parser.add_argument(
        "--card",
        default="models/model_card.md",
        type=Path,
        help="모델 선정 근거 마크다운 (매 실행 시 timestamp 사본도 함께 저장)",
    )
    parser.add_argument(
        "--note",
        default="",
        type=str,
        help="이번 학습의 변경 노트 (models/training_history.md에 함께 기록)",
    )
    args = parser.parse_args()

    if not args.features.exists():
        raise SystemExit(
            f"feature CSV 없음: {args.features}\n"
            "AI Hub 데이터 → MediaPipe로 features.py 사용해 추출 후 CSV 생성 필요"
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
    rf_metrics = _eval_sklearn(rf, X_test, y_test)
    rf_ms = _measure_inference_time(rf, X_test, "rf")
    print(
        f"RF accuracy={rf_metrics['accuracy']:.3f} "
        f"f1={rf_metrics['f1_macro']:.3f} {rf_ms:.2f} ms/inf"
    )

    print("== MLP 학습 ==")
    mlp = _train_mlp(X_train, y_train, in_dim=X.shape[1], n_classes=len(CLASSES))
    mlp_metrics = _eval_mlp(mlp, X_test, y_test)
    mlp_ms = _measure_inference_time(mlp, X_test, "mlp")
    print(
        f"MLP accuracy={mlp_metrics['accuracy']:.3f} "
        f"f1={mlp_metrics['f1_macro']:.3f} {mlp_ms:.2f} ms/inf"
    )

    # 우수 모델 선정: accuracy 우선, 동률이면 추론 빠른 쪽
    if rf_metrics["accuracy"] > mlp_metrics["accuracy"] or (
        rf_metrics["accuracy"] == mlp_metrics["accuracy"] and rf_ms <= mlp_ms
    ):
        winner, winner_name = rf, "RandomForest"
        metrics, inf_ms = rf_metrics, rf_ms
    else:
        winner, winner_name = mlp, "MLP"
        metrics, inf_ms = mlp_metrics, mlp_ms

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if winner_name == "RandomForest":
        joblib.dump(
            {"model": winner, "scaler": scaler, "kind": "rf", "classes": CLASSES},
            args.out,
        )
    else:
        torch.save(winner.state_dict(), args.out.with_suffix(".pt"))
        joblib.dump(
            {
                "scaler": scaler,
                "kind": "mlp",
                "in_dim": X.shape[1],
                "classes": CLASSES,
            },
            args.out,
        )

    card = (
        f"# Pose Classifier Model Card\n\n"
        f"- 학습 데이터: `{args.features}` (n={len(df)})\n"
        f"- 분할: 80% train / 20% test (stratified)\n"
        f"- 선정 모델: **{winner_name}**\n"
        f"- 정확도: {metrics['accuracy']:.3f}\n"
        f"- F1 macro: {metrics['f1_macro']:.3f}\n"
        f"- 추론 시간 (per inference): {inf_ms:.2f} ms\n\n"
        f"## RF vs MLP 비교\n\n"
        f"| 모델 | accuracy | f1_macro | inference ms |\n"
        f"|---|---|---|---|\n"
        f"| RandomForest | {rf_metrics['accuracy']:.3f} | "
        f"{rf_metrics['f1_macro']:.3f} | {rf_ms:.2f} |\n"
        f"| MLP | {mlp_metrics['accuracy']:.3f} | "
        f"{mlp_metrics['f1_macro']:.3f} | {mlp_ms:.2f} |\n\n"
        f"## 선정 기준\n\n"
        f"정확도가 더 높은 모델 선정. 동률이면 추론 속도가 빠른 모델 선정.\n"
    )
    args.card.write_text(card, encoding="utf-8")

    # 매 실행 timestamp 사본 + training_history.md 한 줄 append (덮어쓰기 방지)
    stamp = time.strftime("%Y-%m-%d_%H%M%S")
    card_archived = args.card.with_name(f"model_card_{stamp}.md")
    card_archived.write_text(card, encoding="utf-8")

    history_path = args.out.parent / "training_history.md"
    if not history_path.exists():
        history_path.write_text(
            "# Pose Classifier 학습 누적 이력\n\n"
            "매 `python -m pose.train` 실행 결과 자동 누적. RF·MLP 비교 + 선정 모델 한눈에 비교.\n\n"
            "| 시각 | n | feat | RF acc | RF f1 | RF ms | MLP acc | MLP f1 | MLP ms | winner | card | note |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    safe_note = (args.note or "-").replace("|", "\\|").replace("\n", " ")
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    row = (
        f"| {now} | {len(df)} | {X.shape[1]} | "
        f"{rf_metrics['accuracy']:.3f} | {rf_metrics['f1_macro']:.3f} | {rf_ms:.2f} | "
        f"{mlp_metrics['accuracy']:.3f} | {mlp_metrics['f1_macro']:.3f} | {mlp_ms:.2f} | "
        f"**{winner_name}** | [{card_archived.name}]({card_archived.name}) | {safe_note} |\n"
    )
    with history_path.open("a", encoding="utf-8") as f:
        f.write(row)

    print(f"\n저장: {args.out} ({winner_name}) + {args.card}")
    print(f"누적 이력 갱신: {history_path}")


if __name__ == "__main__":
    main()
