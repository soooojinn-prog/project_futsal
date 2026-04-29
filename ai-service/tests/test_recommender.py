import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from data_generator import generate_matches
from recommender import Recommender


@pytest.fixture
def rec():
    return Recommender(generate_matches(300))


def test_recommend_returns_list(rec):
    result = rec.recommend("FW", "MALE", 5)
    assert isinstance(result, list)


def test_recommend_returns_at_most_five(rec):
    result = rec.recommend("FW", "MALE", 5)
    assert len(result) <= 5


def test_recommend_returns_ids_in_grade_range():
    import pandas as pd
    df = pd.DataFrame([
        {"matchId": 1, "gender": "MALE", "minGrade": 1, "maxGrade": 3, "region": "서울", "startHour": 10},
        {"matchId": 2, "gender": "MALE", "minGrade": 5, "maxGrade": 8, "region": "서울", "startHour": 10},
    ])
    rec = Recommender(df)
    result = rec.recommend("FW", "MALE", 2)
    assert 1 in result
    assert 2 not in result


def test_recommend_fallback_when_no_grade_match():
    import pandas as pd
    df = pd.DataFrame([
        {"matchId": 1, "gender": "MALE", "minGrade": 1, "maxGrade": 2, "region": "서울", "startHour": 10},
    ])
    rec = Recommender(df)
    result = rec.recommend("FW", "MALE", 99)
    assert isinstance(result, list)


def test_recommend_gender_filter():
    import pandas as pd
    df = pd.DataFrame([
        {"matchId": 1, "gender": "FEMALE", "minGrade": 1, "maxGrade": 10, "region": "서울", "startHour": 10},
        {"matchId": 2, "gender": "MALE",   "minGrade": 1, "maxGrade": 10, "region": "서울", "startHour": 10},
        {"matchId": 3, "gender": "ALL",    "minGrade": 1, "maxGrade": 10, "region": "서울", "startHour": 10},
    ])
    rec = Recommender(df)
    result = rec.recommend("FW", "MALE", 5)
    assert 1 not in result
    assert 2 in result or 3 in result
