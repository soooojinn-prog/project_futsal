"""AI Hub 축구 킥 데이터셋 2D 라벨 JSON → feature CSV 변환.

각 JSON 한 장(= 한 카메라가 본 한 frame)을 한 샘플로 간주하여 22점 키포인트에서
관절 각도·상대 위치 feature를 계산하고 metaData의 'kick type'을 label로 매핑.

사용법:
    python -m pose.extract_features \\
        --labels-dirs data/pose_labels/INSIDE_KICK_2D_f data/pose_labels/INSTEP_KICK_2D_f \\
        --out data/pose_features.csv \\
        --max-per-class 4000   # 클래스 불균형 완화 (None이면 전체)

출력 CSV 컬럼 (14 feature + label):
    좌/우 절대각 6개: left_knee_angle, right_knee_angle, left_hip_angle,
                       right_hip_angle, left_ankle_angle, right_ankle_angle
    체격 2개: torso_lean, hip_width
    좌/우 derived 6개: knee_diff, knee_max, knee_min,
                       ankle_diff, ankle_max, hip_diff
    label

* kick/plant 대신 좌/우 대칭 derived feature(차이·극값)로 차는 발 정보를 모델이
  암묵적으로 학습. 추론 시에도 동일 14차원 (kicking foot 정보 불필요).
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import pandas as pd

LABEL_MAP = {
    "인사이드": "INSIDE_KICK",
    "인스텝": "INSTEP_KICK",
    "인프런트": "INFRONT_KICK",
}


def _joint_angle(p1: dict | None, p2: dict | None, p3: dict | None) -> float:
    """세 점 (p2 정점) 사이의 각도(°). None이거나 길이 0이면 0 반환."""
    if not (p1 and p2 and p3):
        return 0.0
    v1 = (p1["x"] - p2["x"], p1["y"] - p2["y"])
    v2 = (p3["x"] - p2["x"], p3["y"] - p2["y"])
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    cos = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(cos))


def _dist(p1: dict | None, p2: dict | None) -> float:
    if not (p1 and p2):
        return 0.0
    return math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"])


def extract_features_from_json(label: dict) -> dict | None:
    """단일 JSON에서 feature dict 생성 (label 컬럼 포함). 실패 시 None."""
    meta = label.get("metaData", {})
    kick_type_ko = meta.get("kick type", "")
    label_str = LABEL_MAP.get(kick_type_ko)
    if label_str is None:
        return None

    pose_loc: dict | None = None
    for ann in label.get("annotation", []):
        if "pose" in ann:
            pose_loc = ann["pose"].get("location")
            break
    if pose_loc is None:
        return None

    g = pose_loc.get

    left_knee = _joint_angle(g("왼쪽 엉덩이"), g("왼쪽 무릎"), g("왼쪽 발목"))
    right_knee = _joint_angle(g("오른쪽 엉덩이"), g("오른쪽 무릎"), g("오른쪽 발목"))
    left_hip = _joint_angle(g("왼쪽 어깨"), g("왼쪽 엉덩이"), g("왼쪽 무릎"))
    right_hip = _joint_angle(g("오른쪽 어깨"), g("오른쪽 엉덩이"), g("오른쪽 무릎"))
    left_ankle = _joint_angle(g("왼쪽 무릎"), g("왼쪽 발목"), g("왼쪽 엄지발가락"))
    right_ankle = _joint_angle(g("오른쪽 무릎"), g("오른쪽 발목"), g("오른쪽 엄지발가락"))

    # 상체 기울기: 어깨 중점 vs 엉덩이 중점 → 수직축 대비 기울기
    sh_l, sh_r = g("왼쪽 어깨"), g("오른쪽 어깨")
    hp_l, hp_r = g("왼쪽 엉덩이"), g("오른쪽 엉덩이")
    torso_lean = 0.0
    if sh_l and sh_r and hp_l and hp_r:
        sh_mid_x = (sh_l["x"] + sh_r["x"]) / 2
        sh_mid_y = (sh_l["y"] + sh_r["y"]) / 2
        hp_mid_x = (hp_l["x"] + hp_r["x"]) / 2
        hp_mid_y = (hp_l["y"] + hp_r["y"]) / 2
        dx = sh_mid_x - hp_mid_x
        dy = sh_mid_y - hp_mid_y
        if abs(dy) > 1e-6:
            torso_lean = math.degrees(math.atan2(dx, -dy))

    hip_width = _dist(hp_l, hp_r)

    return {
        "left_knee_angle": left_knee,
        "right_knee_angle": right_knee,
        "left_hip_angle": left_hip,
        "right_hip_angle": right_hip,
        "left_ankle_angle": left_ankle,
        "right_ankle_angle": right_ankle,
        "torso_lean": torso_lean,
        "hip_width": hip_width,
        # derived symmetric — 차는 발 정보 없이도 좌/우 비대칭 패턴 학습
        "knee_diff": abs(left_knee - right_knee),
        "knee_max": max(left_knee, right_knee),
        "knee_min": min(left_knee, right_knee),
        "ankle_diff": abs(left_ankle - right_ankle),
        "ankle_max": max(left_ankle, right_ankle),
        "hip_diff": abs(left_hip - right_hip),
        "label": label_str,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--labels-dirs",
        nargs="+",
        required=True,
        type=Path,
        help="JSON 라벨 디렉토리 (여러 개 지정 가능)",
    )
    parser.add_argument("--out", default=Path("data/pose_features.csv"), type=Path)
    parser.add_argument(
        "--max-per-class",
        default=None,
        type=int,
        help="클래스당 최대 샘플 수 (불균형 완화용). 미지정 시 전체.",
    )
    parser.add_argument("--seed", default=42, type=int)
    parser.add_argument(
        "--camera-filter",
        default=None,
        type=str,
        help="파일명에 이 패턴이 포함된 JSON만 사용 (예: 'a-01'로 정면 카메라만)",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    rows: list[dict] = []
    for d in args.labels_dirs:
        if not d.exists():
            print(f"[skip] {d} 없음")
            continue
        files = list(d.rglob("*.json"))
        if args.camera_filter:
            files = [f for f in files if args.camera_filter in f.name]
        print(f"{d}: {len(files)}개 JSON 발견 (filter={args.camera_filter or 'none'})")
        for jf in files:
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
            except Exception:
                continue
            feat = extract_features_from_json(data)
            if feat is not None:
                rows.append(feat)

    df = pd.DataFrame(rows)
    if df.empty:
        raise SystemExit("샘플 0개 — labels-dirs 확인")

    print("\n전체 label 분포:")
    print(df["label"].value_counts())

    if args.max_per_class is not None:
        balanced: list[pd.DataFrame] = []
        for cls, sub in df.groupby("label"):
            n = min(len(sub), args.max_per_class)
            balanced.append(sub.sample(n=n, random_state=args.seed))
        df = pd.concat(balanced, ignore_index=True).sample(
            frac=1.0, random_state=args.seed
        )
        print(f"\n다운샘플링 후 (max-per-class={args.max_per_class}):")
        print(df["label"].value_counts())

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")
    print(f"\n총 {len(df)} sample 저장: {args.out}")


if __name__ == "__main__":
    main()
