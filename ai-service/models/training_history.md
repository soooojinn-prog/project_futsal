# Pose Classifier 학습 누적 이력

매 `python -m pose.train` 실행 결과 자동 누적. RF·MLP 비교 + 선정 모델 한눈에 비교.

| 시각 | n | feat | RF acc | RF f1 | RF ms | MLP acc | MLP f1 | MLP ms | winner | card | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-22 13:00 | 8000 | 12 | 0.942 | 0.942 | 17.18 | 0.889 | 0.889 | 0.09 | **RandomForest** | (사전 backfill) | 1차 — 인사이드 여 4000 + 인스텝 여 4000, kick/plant 포함 12 feature |
| 2026-05-22 14:00 | 8000 | 8 | 0.861 | 0.861 | 17.16 | 0.713 | 0.713 | 0.03 | **RandomForest** | (사전 backfill) | 2차 — 여만, kick/plant 제거하고 좌·우 절대각 + torso_lean + hip_width 8 feature (추론 호환성 확보) |
| 2026-05-22 14:30 | 16000 | 8 | 0.682 | 0.682 | 23.02 | 0.547 | 0.547 | 0.07 | **RandomForest** | (사전 backfill) | 3차 — 남+여 통합 8000+8000으로 데이터 증강, feature 그대로 8개. 성별·체격 다양성 흡수 못해 정확도 하락 |
| 2026-05-22 14:50 | 16000 | 14 | 0.680 | 0.680 | 20.85 | 0.579 | 0.579 | 0.06 | **RandomForest** | (사전 backfill) | 4차 — 남+여 + symmetric derived feature 6개 추가 (knee_diff/max/min, ankle_diff/max, hip_diff) 8→14 feature. 정확도 거의 변화 없음 — frame 단위 sample이 너무 다양 |
| 2026-05-22 15:28:05 | 8000 | 14 | 0.781 | 0.781 | 21.94 | 0.670 | 0.670 | 0.05 | **RandomForest** | [model_card_2026-05-22_152805.md](model_card_2026-05-22_152805.md) | 5차 — 카메라 a-01 정면만 필터, 남+여 + 14 feat (다양성 1/8로 축소) |
| 2026-05-22 15:32:34 | 8000 | 18 | 0.786 | 0.786 | 21.63 | 0.667 | 0.667 | 0.05 | **RandomForest** | [model_card_2026-05-22_153234.md](model_card_2026-05-22_153234.md) | 7차 — a-01 카메라 + kick/plant 4개 부활(학습은 metadata, 추론은 무릎각 max/min heuristic). 18 feature |
| 2026-05-26 20:57:17 | 3966 | 18 | 0.942 | 0.864 | 17.92 | 0.907 | 0.721 | 0.15 | **RandomForest** | [model_card_2026-05-26_205717.md](model_card_2026-05-26_205717.md) | 8차 — 여성만 + a-01 + 18 feat (1차 0.942 패턴 재현 + 추론 호환 보장) |
