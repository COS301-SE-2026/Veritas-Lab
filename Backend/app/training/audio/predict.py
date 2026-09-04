from pathlib import Path

import torch
import librosa

from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

PROJECT_ROOT = Path(__file__).resolve().parents[4]
OUTPUT_DIR = PROJECT_ROOT /"models" / "audio"

device = torch.device("cpu")

def load_model():
    feature_extractor = AutoFeatureExtractor.from_pretrained(OUTPUT_DIR)

    model = AutoModelForAudioClassification.from_pretrained(OUTPUT_DIR)
    model.to(device)
    model.eval()

    return model, feature_extractor

model, feature_extractor = load_model()

def predict_audio(file_path: str):
    audio, _ = librosa.load(file_path, sr=16000, mono=True)
    max_length = 16000 * 4

    inputs = feature_extractor(
        audio,
        sampling_rate=16000,
        return_tensors="pt",
        padding="max_length",
        max_length=max_length,
        truncation=True
    )

    inputs = {
        key: value.to(device)
        for key, value
        in inputs.items()
    }

    with torch.no_grad():
        outputs = model(**inputs)

    probabilities = torch.softmax(outputs.logits, dim=-1)[0]

    predicted_id = probabilities.argmax().item()
    confidence = probabilities[predicted_id].item()

    label = model.config.id2label[predicted_id]

    return {
        "label": label,
        "confidence": confidence,
        "authentic_probability":probabilities[0].item(),
        "ai_probability":probabilities[1].item()
    }


if __name__ == "__main__":
    test_file = input("Audio file path: ")
    result = predict_audio(test_file)
    print(result)
