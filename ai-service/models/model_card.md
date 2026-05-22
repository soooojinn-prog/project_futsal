# Pose Classifier Model Card

- 학습 데이터: `data\pose_features.csv` (n=16000)
- 분할: 80% train / 20% test (stratified)
- 선정 모델: **RandomForest**
- 정확도: 0.680
- F1 macro: 0.680
- 추론 시간 (per inference): 20.85 ms

## RF vs MLP 비교

| 모델 | accuracy | f1_macro | inference ms |
|---|---|---|---|
| RandomForest | 0.680 | 0.680 | 20.85 |
| MLP | 0.579 | 0.579 | 0.06 |

## 선정 기준

정확도가 더 높은 모델 선정. 동률이면 추론 속도가 빠른 모델 선정.
