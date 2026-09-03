import pytest
import torch
from unittest.mock import MagicMock, patch

from app.training.audio.dataset import audio_dataset

@pytest.fixture
def dataset_directory(tmp_path):
    authentic_dir = tmp_path / "0_authentic"
    ai_dir = tmp_path / "1_ai"

    authentic_dir.mkdir()
    ai_dir.mkdir()

    (authentic_dir / "authentic1.wav").touch()
    (authentic_dir / "authentic2.mp3").touch()

    (ai_dir / "ai1.flac").touch()
    (ai_dir / "ai2.ogg").touch()

    (authentic_dir / "ignore.txt").touch()
    (ai_dir / "ignore.json").touch()

    return tmp_path

@pytest.fixture
def mock_feature_extractor():
    extractor = MagicMock()

    extractor.return_value = {
        "input_values": torch.tensor(
            [[0.1, 0.2, 0.3, 0.4]],
            dtype=torch.float32
        )
    }

    return extractor


def test_dataset_loads_valid_audio_files(dataset_directory, mock_feature_extractor):
    dataset = audio_dataset(dataset_directory, mock_feature_extractor)

    assert len(dataset.samples) == 4

def test_dataset_assigns_correct_labels(dataset_directory, mock_feature_extractor):
    dataset = audio_dataset(dataset_directory, mock_feature_extractor)

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

def test_dataset_ignores_unsupported_files(dataset_directory, mock_feature_extractor):
    dataset = audio_dataset(dataset_directory, mock_feature_extractor)

    file_extensions = {
        file_path.suffix.lower()
        for file_path, _ in dataset.samples
    }

    assert ".txt" not in file_extensions
    assert ".json" not in file_extensions

def test_dataset_length(dataset_directory, mock_feature_extractor):
    dataset = audio_dataset(dataset_directory, mock_feature_extractor)

    assert len(dataset) == 4

def test_default_sample_rate_and_max_length(dataset_directory, mock_feature_extractor):
    dataset = audio_dataset(dataset_directory, mock_feature_extractor)

    assert dataset.sample_rate == 16000
    assert dataset.max_length == 64000

def test_custom_max_seconds(dataset_directory, mock_feature_extractor):
    dataset = audio_dataset(
        dataset_directory,
        mock_feature_extractor,
        max_seconds=2
    )

    assert dataset.max_length == 32000

@patch("app.training.audio.dataset.librosa.load")
def test_getitem_loads_audio_correctly(mock_librosa_load, dataset_directory, mock_feature_extractor):
    fake_audio = [0.1, 0.2, 0.3]

    mock_librosa_load.return_value = fake_audio, 16000

    dataset = audio_dataset(dataset_directory, mock_feature_extractor)
    dataset[0]

    mock_librosa_load.assert_called_once_with(
        dataset.samples[0][0],
        sr=16000,
        mono=True
    )

@patch("app.training.audio.dataset.librosa.load")
def test_getitem_calls_feature_extractor_correctly(mock_librosa_load, dataset_directory, mock_feature_extractor):
    fake_audio = [0.1, 0.2, 0.3]

    mock_librosa_load.return_value = (fake_audio, 16000)

    dataset = audio_dataset(dataset_directory, mock_feature_extractor)
    dataset[0]

    mock_feature_extractor.assert_called_once_with(
        fake_audio,
        sampling_rate=16000,
        max_length=64000,
        truncation=True,
        padding="max_length",
        return_tensors="pt"
    )

@patch("app.training.audio.dataset.librosa.load")
def test_getitem_returns_input_values(mock_librosa_load, dataset_directory, mock_feature_extractor):
    mock_librosa_load.return_value = [0.1, 0.2, 0.3], 16000
    dataset = audio_dataset(dataset_directory, mock_feature_extractor)
    result = dataset[0]

    assert "input_values" in result

    assert torch.equal(
        result["input_values"],
        torch.tensor(
            [0.1, 0.2, 0.3, 0.4],
            dtype=torch.float32
        )
    )

@patch("app.training.audio.dataset.librosa.load")
def test_getitem_returns_correct_label(mock_librosa_load, dataset_directory, mock_feature_extractor):
    mock_librosa_load.return_value = [0.1, 0.2, 0.3], 16000
    dataset = audio_dataset(dataset_directory, mock_feature_extractor)
    result = dataset[0]

    assert torch.equal(result["labels"], torch.tensor(0, dtype=torch.long))

@patch("app.training.audio.dataset.librosa.load")
def test_ai_sample_returns_label_one(mock_librosa_load, dataset_directory, mock_feature_extractor):
    mock_librosa_load.return_value = [0.1, 0.2, 0.3], 16000
    

    dataset = audio_dataset(dataset_directory, mock_feature_extractor)

    ai_index = next(
        index
        for index, (_, label) in enumerate(dataset.samples)
        if label == 1
    )

    result = dataset[ai_index]

    assert result["labels"].item() == 1
    assert result["labels"].dtype == torch.long

def test_empty_dataset(tmp_path, mock_feature_extractor):
    (tmp_path / "0_authentic").mkdir()
    (tmp_path / "1_ai").mkdir()

    dataset = audio_dataset(tmp_path, mock_feature_extractor)

    assert len(dataset) == 0
    assert dataset.samples == []