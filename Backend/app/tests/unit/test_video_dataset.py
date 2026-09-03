from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch

from app.training.video.dataset import (
    CLIP_MEAN,
    CLIP_STD,
    VIDEO_EXTENSIONS,
    read_video_frames,
    uniform_frame_indices,
    video_binary_dataset
)

def test_uniform_frame_indices():
    indices = uniform_frame_indices(total_frames=10, num_frames=4)
    expected = np.array([0, 3, 6, 9], dtype=np.int64)
    assert np.array_equal(indices, expected)

def test_uniform_frame_indices_single_frame():
    indices = uniform_frame_indices(total_frames=1, num_frames=4)
    expected = np.array([0, 0, 0, 0], dtype=np.int64)
    assert np.array_equal(indices, expected)

def test_uniform_frame_indices_raises_for_no_frames():
    with pytest.raises(
        ValueError,
        match="Video contains no decodable frames"
    ):
        uniform_frame_indices(total_frames=0, num_frames=8)

def test_video_extensions():
    assert ".mp4" in VIDEO_EXTENSIONS
    assert ".mov" in VIDEO_EXTENSIONS
    assert ".avi" in VIDEO_EXTENSIONS
    assert ".mkv" in VIDEO_EXTENSIONS
    assert ".webm" in VIDEO_EXTENSIONS
    assert ".m4v" in VIDEO_EXTENSIONS

@patch("app.training.video.dataset.cv2.VideoCapture")
def test_read_video_frames_raises_when_video_cannot_open(mock_video_capture):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False

    mock_video_capture.return_value = mock_cap

    with pytest.raises(
        RuntimeError,
        match="Could not open video"
    ):
        read_video_frames("broken.mp4")

@patch("app.training.video.dataset.cv2.VideoCapture")
def test_read_video_frames_raises_when_no_frames_decoded(mock_video_capture):
    mock_cap = MagicMock()

    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 4
    mock_cap.read.return_value = False, None
    mock_video_capture.return_value = mock_cap

    with pytest.raises(
        RuntimeError,
        match="No frames decoded from"
    ):
        read_video_frames("test.mp4", num_frames=2)

    mock_cap.release.assert_called_once()

@patch("app.training.video.dataset.cv2.resize")
@patch("app.training.video.dataset.cv2.cvtColor")
@patch("app.training.video.dataset.cv2.VideoCapture")
def test_read_video_frames_returns_tensor(mock_video_capture, mock_cvt_color, mock_resize):
    mock_cap = MagicMock()

    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 3

    frame0 = np.ones((10, 10, 3), dtype=np.uint8) * 10
    frame1 = np.ones((10, 10, 3), dtype=np.uint8) * 20
    frame2 = np.ones((10, 10, 3), dtype=np.uint8) * 30

    mock_cap.read.side_effect = [
        (True, frame0),
        (True, frame1),
        (True, frame2),
        (False, None)
    ]

    mock_video_capture.return_value = mock_cap
    mock_cvt_color.side_effect = lambda frame, _: frame
    mock_resize.side_effect = lambda frame, size, interpolation: np.resize(frame, (size[1], size[0], 3))

    result = read_video_frames("video.mp4", num_frames=3, image_size=4)

    assert isinstance(result, torch.Tensor)
    assert result.shape == (3, 3, 4, 4)
    assert result.dtype == torch.float32

    mock_video_capture.assert_called_once_with("video.mp4")
    mock_cap.release.assert_called_once()

@patch("app.training.video.dataset.cv2.resize")
@patch("app.training.video.dataset.cv2.cvtColor")
@patch("app.training.video.dataset.cv2.VideoCapture")
def test_read_video_frames_converts_and_resizes_selected_frames(mock_video_capture, mock_cvt_color, mock_resize):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 2

    frame = np.zeros((8, 8, 3), dtype=np.uint8)

    mock_cap.read.side_effect = [
        (True, frame),
        (True, frame),
        (False, None)
    ]

    mock_video_capture.return_value = mock_cap
    converted = np.ones((8, 8, 3), dtype=np.uint8)
    resized = np.ones((4, 4, 3), dtype=np.uint8)
    mock_cvt_color.return_value = converted
    mock_resize.return_value = resized

    result = read_video_frames("video.mp4", num_frames=2, image_size=4)

    assert mock_cvt_color.call_count == 2
    assert mock_resize.call_count == 2
    assert result.shape == (2, 3, 4, 4)

@patch("app.training.video.dataset.cv2.resize")
@patch("app.training.video.dataset.cv2.cvtColor")
@patch("app.training.video.dataset.cv2.VideoCapture")
def test_read_video_frames_uses_nearest_available_frame(mock_video_capture, mock_cvt_color, mock_resize):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 5

    frame0 = np.zeros((4, 4, 3), dtype=np.uint8)
    frame1 = np.ones((4, 4, 3), dtype=np.uint8) * 10

    mock_cap.read.side_effect = [
        (True, frame0),
        (True, frame1),
        (False, None)
    ]

    mock_video_capture.return_value = mock_cap

    mock_cvt_color.side_effect = lambda frame, _: frame
    mock_resize.side_effect = lambda frame, size, interpolation: frame

    result = read_video_frames("video.mp4", num_frames=4, image_size=4)
    assert isinstance(result, torch.Tensor)
    assert result.shape[0] == 4

def test_clip_constants():
    assert CLIP_MEAN.shape == (3,)
    assert CLIP_STD.shape == (3,)
    assert CLIP_MEAN.dtype == np.float32
    assert CLIP_STD.dtype == np.float32

def test_dataset_loads_authentic_and_ai_videos(tmp_path):
    authentic_dir = tmp_path / "0_authentic"
    ai_dir = tmp_path / "1_ai"

    authentic_dir.mkdir()
    ai_dir.mkdir()

    (authentic_dir / "real.mp4").touch()
    (authentic_dir / "real.mov").touch()

    (ai_dir / "fake.avi").touch()
    (ai_dir / "fake.mkv").touch()

    dataset = video_binary_dataset(tmp_path)

    assert len(dataset) == 4

    authentic_samples = [
        sample
        for sample in dataset.samples
        if sample[1] == 0
    ]

    ai_samples = [
        sample
        for sample in dataset.samples
        if sample[1] == 1
    ]

    assert len(authentic_samples) == 2
    assert len(ai_samples) == 2

def test_dataset_ignores_invalid_extensions(tmp_path):
    authentic_dir = tmp_path / "0_authentic"
    ai_dir = tmp_path / "1_ai"

    authentic_dir.mkdir()
    ai_dir.mkdir()

    (authentic_dir / "real.mp4").touch()
    (authentic_dir / "ignore.txt").touch()

    (ai_dir / "fake.webm").touch()
    (ai_dir / "ignore.jpg").touch()

    dataset = video_binary_dataset(tmp_path)

    assert len(dataset) == 2

    extensions = {
        path.suffix.lower()
        for path, _ in dataset.samples
    }

    assert ".txt" not in extensions
    assert ".jpg" not in extensions

def test_dataset_supports_nested_directories(tmp_path):
    authentic_dir = tmp_path / "0_authentic" / "nested"
    ai_dir = tmp_path /"1_ai" /"nested"
    authentic_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)

    (authentic_dir / "real.mp4").touch()
    (ai_dir / "fake.mp4").touch()

    dataset = video_binary_dataset(tmp_path)
    assert len(dataset) == 2

def test_dataset_handles_missing_class_directory(tmp_path):
    authentic_dir = tmp_path / "0_authentic"
    authentic_dir.mkdir()

    (authentic_dir / "real.mp4").touch()

    dataset = video_binary_dataset(tmp_path)

    assert len(dataset) == 1
    assert dataset.samples[0][1] == 0

def test_dataset_raises_when_no_videos_found(tmp_path):
    (tmp_path / "0_authentic").mkdir()
    (tmp_path / "1_ai").mkdir()

    with pytest.raises(
        RuntimeError,
        match="No videos found under"
    ):
        video_binary_dataset(tmp_path)

def test_dataset_length(tmp_path):
    authentic_dir = tmp_path / "0_authentic"
    ai_dir = tmp_path / "1_ai"

    authentic_dir.mkdir()
    ai_dir.mkdir()

    (authentic_dir / "one.mp4").touch()
    (ai_dir / "two.mp4").touch()

    dataset = video_binary_dataset(tmp_path)
    assert len(dataset) == 2

@patch("app.training.video.dataset.read_video_frames")
def test_dataset_getitem(mock_read_video_frames, tmp_path):
    authentic_dir = tmp_path / "0_authentic"
    authentic_dir.mkdir()
    video_path = authentic_dir / "real.mp4"
    video_path.touch()

    fake_video = torch.zeros((8, 3, 224, 224))
    mock_read_video_frames.return_value = fake_video
    dataset = video_binary_dataset(tmp_path, num_frames=8, image_size=224)

    result = dataset[0]
    mock_read_video_frames.assert_called_once_with(video_path, num_frames=8, image_size=224)

    assert torch.equal(result["video"], fake_video)
    assert result["label"].item() == 0
    assert result["label"].dtype == torch.float32
    assert result["path"] == str(video_path)

@patch("app.training.video.dataset.read_video_frames")
def test_dataset_getitem_ai_label(mock_read_video_frames, tmp_path):
    ai_dir = tmp_path / "1_ai"
    ai_dir.mkdir()

    video_path = ai_dir / "fake.mp4"
    video_path.touch()

    mock_read_video_frames.return_value = (torch.zeros((4, 3, 64, 64)))
    dataset = video_binary_dataset(tmp_path, num_frames=4, image_size=64)
    result = dataset[0]

    assert result["label"].item() == 1
    assert result["label"].dtype == torch.float32

    mock_read_video_frames.assert_called_once_with(video_path, num_frames=4, image_size=64)