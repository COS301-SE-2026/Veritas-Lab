from pathlib import Path
import librosa
import torch
from torch.utils.data import Dataset

class audio_dataset(Dataset):
    def __init__(
        self,
        root_dir,
        feature_extractor,
        max_seconds=4
    ):
        self.root_dir = Path(root_dir)
        self.feature_extractor = feature_extractor

        self.sample_rate = 16000
        self.max_length = self.sample_rate * max_seconds

        self.samples = []

        authentic_dir = self.root_dir / "0_authentic"
        ai_dir = self.root_dir / "1_ai"

        for file in sorted(authentic_dir.glob("*")):
            if file.suffix.lower() in {".wav", ".flac", ".mp3", ".ogg", ".m4a"}:
                self.samples.append((file, 0))

        for file in sorted(ai_dir.glob("*")):
            if file.suffix.lower() in {".wav", ".flac", ".mp3", ".ogg", ".m4a"}:
                self.samples.append((file, 1))

        print(f"Loaded {len(self.samples)} files from {self.root_dir}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        file_path, label = self.samples[index]

        audio, _ = librosa.load(file_path, sr=self.sample_rate, mono=True)

        inputs = self.feature_extractor(
            audio,
            sampling_rate=self.sample_rate,
            max_length=self.max_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt"
        )

        return {
            "input_values":
                inputs["input_values"].squeeze(0),

            "labels":
                torch.tensor(
                    label,
                    dtype=torch.long
                )
        }
