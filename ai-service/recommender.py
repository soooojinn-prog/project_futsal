import pandas as pd

GENDER_COMPAT = {
    "MALE":   {"MALE", "ALL"},
    "FEMALE": {"FEMALE", "ALL"},
    "ALL":    {"MALE", "FEMALE", "ALL"},
}


class Recommender:
    def __init__(self, matches: pd.DataFrame):
        self.matches = matches.copy()

    def recommend(self, position: str, gender: str, grade: int, top_n: int = 5) -> list[int]:
        df = self.matches.copy()

        # grade 범위 필터
        grade_filtered = df[(df["minGrade"] <= grade) & (df["maxGrade"] >= grade)]

        # gender 필터
        compat = GENDER_COMPAT.get(gender, {"ALL"})
        gender_filtered = grade_filtered[grade_filtered["gender"].isin(compat)]

        # 필터 후 비어있으면 fallback: 최신 매치 상위 top_n
        if gender_filtered.empty:
            return list(self.matches["matchId"].head(top_n).astype(int))

        # grade 중간값과 유저 grade의 거리로 점수 계산 (가까울수록 높은 점수)
        df2 = gender_filtered.copy()
        df2["gradeMid"] = (df2["minGrade"] + df2["maxGrade"]) / 2
        df2["score"] = 1 / (1 + abs(df2["gradeMid"] - grade))
        top = df2.nlargest(top_n, "score")
        return list(top["matchId"].astype(int))
