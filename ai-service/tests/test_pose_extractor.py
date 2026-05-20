from unittest.mock import MagicMock, patch

import numpy as np

from pose.extractor import PoseExtractor


def _fake_frame(h=480, w=640):
    return np.zeros((h, w, 3), dtype=np.uint8)


def test_extractor_returns_one_landmark_set_per_frame():
    fake_landmark = MagicMock()
    fake_landmark.landmark = [
        MagicMock(x=0.5, y=0.5, z=0.0, visibility=0.9) for _ in range(33)
    ]
    fake_pose = MagicMock()
    fake_pose.process.return_value = MagicMock(pose_landmarks=fake_landmark)

    with patch("pose.extractor.mp.solutions.pose.Pose", return_value=fake_pose):
        ext = PoseExtractor(sample_fps=10)
        frames = [_fake_frame() for _ in range(5)]
        result = ext.extract_from_frames(frames)

    assert len(result) == 5
    assert len(result[0]) == 33
    assert all(p["visibility"] >= 0 for p in result[0])


def test_extractor_skips_frames_with_no_landmarks():
    fake_pose = MagicMock()
    fake_pose.process.return_value = MagicMock(pose_landmarks=None)

    with patch("pose.extractor.mp.solutions.pose.Pose", return_value=fake_pose):
        ext = PoseExtractor(sample_fps=10)
        frames = [_fake_frame() for _ in range(3)]
        result = ext.extract_from_frames(frames)

    assert result == []


def test_extract_from_video_path_uses_cv2():
    fake_cap = MagicMock()
    fake_cap.isOpened.return_value = True
    fake_cap.get.side_effect = lambda x: {5: 30.0, 7: 60}.get(x, 0)
    fake_cap.read.side_effect = [(True, _fake_frame()), (True, _fake_frame()), (False, None)]

    fake_pose = MagicMock()
    fake_pose.process.return_value = MagicMock(pose_landmarks=None)

    with patch("pose.extractor.cv2.VideoCapture", return_value=fake_cap), patch(
        "pose.extractor.mp.solutions.pose.Pose", return_value=fake_pose
    ):
        ext = PoseExtractor(sample_fps=10)
        frames = ext._sample_frames("dummy.mp4")
    assert len(frames) >= 1


def test_max_frames_cap():
    fake_pose = MagicMock()
    fake_pose.process.return_value = MagicMock(
        pose_landmarks=MagicMock(
            landmark=[MagicMock(x=0, y=0, z=0, visibility=1) for _ in range(33)]
        )
    )
    with patch("pose.extractor.mp.solutions.pose.Pose", return_value=fake_pose):
        ext = PoseExtractor(sample_fps=10, max_frames=10)
        frames = [_fake_frame() for _ in range(50)]
        result = ext.extract_from_frames(frames)
    assert len(result) == 10
