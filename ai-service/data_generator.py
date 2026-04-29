import random
import pandas as pd

GENDERS = ["MALE", "FEMALE", "ALL"]
REGIONS = ["서울", "경기", "부산", "대구", "인천", "광주", "대전", "수원"]


def generate_matches(count: int) -> pd.DataFrame:
    records = []
    for i in range(1, count + 1):
        min_grade = random.randint(1, 8)
        max_grade = min(min_grade + random.randint(1, 3), 10)
        records.append({
            "matchId": i,
            "gender": random.choice(GENDERS),
            "minGrade": min_grade,
            "maxGrade": max_grade,
            "region": random.choice(REGIONS),
            "startHour": random.randint(6, 22),
        })
    return pd.DataFrame(records)
