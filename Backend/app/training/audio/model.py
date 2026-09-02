import torch
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

MODEL_ID = "microsoft/wavlm-base"
device = torch.device("cpu")
feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_ID)
model = AutoModelForAudioClassification.from_pretrained(MODEL_ID, num_labels=2)

model.config.id2label = {
    0: "AUTHENTIC",
    1: "AI"
}

model.config.label2id = {
    "AUTHENTIC": 0,
    "AI": 1
}

for param in model.wavlm.parameters():
    param.requires_grad = False

model.to(device)