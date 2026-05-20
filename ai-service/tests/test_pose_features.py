import pytest

from pose.features import FeatureBuilder


def _flat_landmarks(coords: dict[int, tuple[float, float]]) -> list[dict]:
    """idx → (x, y) 매핑을 33점 리스트로 변환."""
    pts = []
    for i in range(33):
        x, y = coords.get(i, (0.0, 0.0))
        pts.append({"x": x, "y": y, "z": 0.0, "visibility": 1.0})
    return pts


def test_angle_180_when_collinear():
    coords = {23: (0.0, 0.0), 25: (0.0, 1.0), 27: (0.0, 2.0)}
    fb = FeatureBuilder()
    angle = fb._joint_angle(_flat_landmarks(coords), 23, 25, 27)
    assert 178.0 <= angle <= 180.0


def test_angle_90_when_right_angle():
    coords = {23: (0.0, 0.0), 25: (1.0, 0.0), 27: (1.0, 1.0)}
    fb = FeatureBuilder()
    angle = fb._joint_angle(_flat_landmarks(coords), 23, 25, 27)
    assert 88.0 <= angle <= 92.0


def test_build_returns_fixed_length_vector():
    coords = {i: (i * 0.01, i * 0.02) for i in range(33)}
    fb = FeatureBuilder()
    vec = fb.build_single([_flat_landmarks(coords) for _ in range(5)])
    assert len(vec) == fb.feature_dim()
    assert all(isinstance(v, float) for v in vec)


def test_build_empty_raises():
    fb = FeatureBuilder()
    with pytest.raises(ValueError):
        fb.build_single([])


def test_feature_dim_is_constant():
    fb1 = FeatureBuilder()
    fb2 = FeatureBuilder()
    assert fb1.feature_dim() == fb2.feature_dim() > 0
