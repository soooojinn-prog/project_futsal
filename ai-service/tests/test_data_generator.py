import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_generator import generate_matches


def test_generate_returns_correct_count():
    df = generate_matches(300)
    assert len(df) == 300


def test_generate_has_required_columns():
    df = generate_matches(10)
    required = {"matchId", "gender", "minGrade", "maxGrade", "region", "startHour"}
    assert required.issubset(set(df.columns))


def test_grade_range_is_valid():
    df = generate_matches(100)
    assert (df["minGrade"] <= df["maxGrade"]).all()


def test_gender_values_are_valid():
    df = generate_matches(100)
    valid = {"MALE", "FEMALE", "ALL"}
    assert set(df["gender"].unique()).issubset(valid)
