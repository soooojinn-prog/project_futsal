"""train.py wrapper — RF/MLP 비교 학습 + 우수 모델 저장.

사용법:
    python -m pose.compare
"""
from . import train

if __name__ == "__main__":
    train.main()
