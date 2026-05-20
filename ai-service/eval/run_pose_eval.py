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


CLASSES = ["GOOD_KICK", "BAD_KICK_KNEE_LOCKED", "GOOD_DRIBBLE", "BAD_DRIBBLE_OVERREACH"]


def _label_from_filename(p: Path) -> str:
    for cls in CLASSES:
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

    from main import _key_angles_from_landmarks

    for v in videos:
        expected = _label_from_filename(v)
        t0 = time.perf_counter()
        landmarks = extractor.extract_from_video(str(v))
        t1 = time.perf_counter()
        if not landmarks:
            results.append(
                {"video": v.name, "expected": expected, "predicted": None, "ok": False}
            )
            continue
        vec = features.build_single(landmarks)
        pred, conf, _ = classifier.predict(vec)
        t2 = time.perf_counter()
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

    return {
        "service_accuracy": correct / max(1, len(videos)),
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
        ok = "✅" if r.get("ok") else "❌"
        lines.append(
            f"| {r['video']} | {r['expected']} | {r.get('predicted', '-')} | "
            f"{ok} | {r.get('total_ms', '-')} |"
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
    print(
        f"service_accuracy={metrics['service_accuracy']:.3f} "
        f"avg_total={metrics['avg_total_ms']}ms"
    )
    print(f"리포트: {args.out}")


if __name__ == "__main__":
    main()
