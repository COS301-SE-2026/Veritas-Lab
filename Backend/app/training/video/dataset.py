from pathlib import Path
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

CLIP_MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
CLIP_STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}

def uniform_frame_indices(total_frames: int, num_frames: int):
    if total_frames <= 0:
        raise ValueError("Video contains no decodable frames")

    return np.linspace(0, total_frames - 1, num_frames).astype(np.int64)

def read_video_frames(path: str | Path, num_frames: int = 8, image_size: int = 224):
    path = str(path)
    cap = cv2.VideoCapture(path)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {path}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = uniform_frame_indices(total, num_frames)

    frames = []
    wanted = set(indices.tolist())
    current = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if current in wanted:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(
                frame,
                (image_size, image_size),
                interpolation=cv2.INTER_AREA
            )
            frames.append((current, frame))

        if len(frames) == len(wanted):
            break

        current += 1

    cap.release()

    if not frames:
        raise RuntimeError(f"No frames decoded from: {path}")

    by_index = {idx: frame for idx, frame in frames}
    sampled = []

    available = sorted(by_index.keys())
    for idx in indices:
        if idx in by_index:
            f = by_index[idx]
        else:
            nearest = min(available, key=lambda x: abs(x - int(idx)))
            f = by_index[nearest]

        sampled.append(f)

    arr = np.stack(sampled).astype(np.float32) / 255.0
    arr = (arr - CLIP_MEAN) / CLIP_STD
    arr = np.transpose(arr, (0, 3, 1, 2))

    return torch.from_numpy(arr)

class video_binary_dataset(Dataset):
    def __init__(
        self,
        root: str | Path,
        num_frames: int = 8,
        image_size: int = 224
    ):
        self.root = Path(root)
        self.num_frames = num_frames
        self.image_size = image_size
        self.samples = []

        for class_name, label in [("0_authentic", 0), ("1_ai", 1)]:
            class_dir = self.root / class_name

            if not class_dir.exists():
                continue

            for path in sorted(class_dir.rglob("*")):
                if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
                    self.samples.append((path, label))

        if not self.samples:
            raise RuntimeError(f"No videos found under {self.root}. Expected 0_authentic/ and 1_ai/ subfolders.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        video = read_video_frames(
            path,
            num_frames=self.num_frames,
            image_size=self.image_size
        )

        return {
            "video": video,
            "label": torch.tensor(label, dtype=torch.float32),
            "path": str(path)
        }