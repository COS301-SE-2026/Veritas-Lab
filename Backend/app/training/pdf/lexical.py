from pathlib import Path
from functools import lru_cache
import pymupdf
import numpy as np 
from datasets import Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)

BASE_DIR = Path(__file__).resolve().parents[2]
MIN_OCR_PAGE_COVERAGE = 0.20
MIN_OCR_IMAGE_HEIGHT = 100
MIN_OCR_IMAGE_WIDTH = 100
TOKENIZER_NAME = "distilroberta-base"
DATASET_ROOT = Path("dataset/pdf")
TRAIN_PATH = DATASET_ROOT / "train"
VALIDATION_PATH = DATASET_ROOT / "validation"
TEST_PATH = DATASET_ROOT / "test"
MODEL_OUTPUT_PATH = BASE_DIR / "ai" / "lexical_detector"
MAX_LENGTH = 512
MIN_TEXT_LENGTH = 30
MAX_TEST_CHUNKS_PER_PDF = 16
INFERENCE_BATCH_SIZE = 8
MAX_TRAINING_CHUNKS_PER_PDF = 8 
# The training is currently way too long, we could consider retraining at a later stage.

@lru_cache
def get_training_tokeniser():
    return AutoTokenizer.from_pretrained(TOKENIZER_NAME)

@lru_cache
def get_inference_model():
    if not MODEL_OUTPUT_PATH.exists():
        raise FileNotFoundError("Lexical model has not been trained yet.")
    
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_OUTPUT_PATH)
    model.eval()
    return model

@lru_cache
def get_inference_tokeniser():
    if not MODEL_OUTPUT_PATH.exists():
        raise FileNotFoundError("Lexical model has not been trained yet.")

    return AutoTokenizer.from_pretrained(MODEL_OUTPUT_PATH)

def create_model():
    return AutoModelForSequenceClassification.from_pretrained(
        TOKENIZER_NAME,
        num_labels=2,
        id2label={
            0: "0_authentic",
            1: "1_ai"
        },

        label2id={
            "0_authentic": 0,
            "1_ai": 1
        }
    )

def get_ocr_text(page, pdf_path, fallback_text):
    try:
        text_page = page.get_textpage_ocr(
            language="eng",
            dpi=300,
            full=True
        )

        ocr_text = page.get_text(
            "text",
            textpage=text_page
        ).strip()

        return ocr_text or fallback_text

    except Exception as e:
        print(f"OCR failed for {pdf_path.name} page {page.number + 1}: {e}")
        return fallback_text

def get_page_text(page, pdf_path):
    page_text = page.get_text("text").strip()

    if len(page_text) >= MIN_TEXT_LENGTH:
        return page_text

    if not page_has_ocr_candidate(page):
        return page_text

    return get_ocr_text(page, pdf_path, page_text)

def extract_pdf_text(pdf_path):
    text = []

    with pymupdf.open(pdf_path) as document:
        for page in document:
            page_text = get_page_text(
                page,
                pdf_path
            )

            if page_text:
                text.append(page_text)

    return "\n".join(text).strip()

def load_split(split_path):
    texts = []
    labels = []
    pdf_ids = []

    classes = {
        "0_authentic": 0,
        "1_ai": 1
    }

    for folder_name, label in classes.items():
        folder = split_path / folder_name

        for pdf_path in folder.glob("*.pdf"):
            text = extract_pdf_text(pdf_path)

            if not text:
                continue

            texts.append(text)
            labels.append(label)
            pdf_ids.append(str(pdf_path))

    print(f"Loaded {len(texts)} PDFs from {split_path}")

    return Dataset.from_dict(
        {
            "text": texts,
            "label": labels,
            "pdf_id": pdf_ids
        }
    )

def pdf_ai_probability(pdf_path, max_chunks=None):
    text = extract_pdf_text(pdf_path)

    if not text:
        return 0.5

    return lexical_ai_probability(text, max_chunks=max_chunks)

def test_model_pdf_level():
    true_labels = []
    predicted_labels = []
    probabilities = []

    classes = {
        "0_authentic": 0,
        "1_ai": 1
    }

    for folder_name, true_label in classes.items():
        folder = TEST_PATH / folder_name

        for pdf_path in folder.glob("*.pdf"):
            probability = pdf_ai_probability(
                pdf_path,
                max_chunks=MAX_TEST_CHUNKS_PER_PDF
            )
            predicted_label = 1 if probability >= 0.5 else 0
            true_labels.append(true_label)
            predicted_labels.append(predicted_label)
            probabilities.append(probability)
            print(
                f"{pdf_path.name}: "
                f"AI probability={probability:.4f}, "
                f"predicted={predicted_label}, "
                f"actual={true_label}"
            )

    if not true_labels:
        raise ValueError("No test PDFs with extractable text were found.")
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_labels,
        predicted_labels,
        average="binary",
        zero_division=0
    )

    accuracy = accuracy_score(
        true_labels,
        predicted_labels
    )

    results = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

    print("\nPDF-level test results:")

    for metric, value in results.items():
        print(f"{metric}: {value:.4f}")

    return results

def prepare_dataset(dataset):
    input_ids = []
    attention_masks = []
    labels = []
    pdf_ids = []
    tokeniser = get_training_tokeniser()

    for example in dataset:
        encoded = tokeniser(
            example["text"],
            truncation=True,
            max_length=MAX_LENGTH,
            return_overflowing_tokens=True,
            padding="max_length"
        )

        chunk_count = min(
            len(encoded["input_ids"]),
            MAX_TRAINING_CHUNKS_PER_PDF
        )

        for i in range(chunk_count):
            input_ids.append(encoded["input_ids"][i])
            attention_masks.append(encoded["attention_mask"][i])
            labels.append(example["label"])
            pdf_ids.append(example["pdf_id"])

    prepared_dataset = Dataset.from_dict(
        {
            "input_ids": input_ids,
            "attention_mask": attention_masks,
            "label": labels
        }
    )

    return prepared_dataset, pdf_ids

def page_has_ocr_candidate(page):
    page_area = page.rect.width * page.rect.height
    if page_area <= 0:
        return False

    for image in page.get_image_info():
        width = image.get("width", 0)
        height = image.get("height", 0)
        bbox = image.get("bbox")

        if(width < MIN_OCR_IMAGE_WIDTH or height < MIN_OCR_IMAGE_HEIGHT):
            continue

        if not bbox:
            continue

        image_area = ((bbox[2] - bbox[0])* (bbox[3] - bbox[1]))

        coverage = image_area / page_area
        if coverage >= MIN_OCR_PAGE_COVERAGE:
            return True

    return False

def create_pdf_metrics(pdf_ids):
    def compute_pdf_metrics(eval_pred):
        logits, labels = eval_pred
        shifted_logits = logits - np.max(
            logits,
            axis=1,
            keepdims=True
        )

        exp_logits = np.exp(shifted_logits)

        probabilities = (exp_logits / np.sum(exp_logits, axis=1, keepdims=True))

        ai_probabilities = probabilities[:, 1]
        pdf_scores = {}
        pdf_labels = {}

        for pdf_id, ai_probability, label in zip(pdf_ids, ai_probabilities, labels):
            if pdf_id not in pdf_scores:
                pdf_scores[pdf_id] = []

            pdf_scores[pdf_id].append(float(ai_probability))
            pdf_labels[pdf_id] = int(label)

        true_labels = []
        predicted_labels = []

        for pdf_id, scores in pdf_scores.items():
            pdf_probability = float(np.mean(scores))
            prediction = (1 if pdf_probability >= 0.5 else 0)

            true_labels.append(pdf_labels[pdf_id])

            predicted_labels.append(prediction)

        precision, recall, f1, _ = (
            precision_recall_fscore_support(
                true_labels,
                predicted_labels,
                average="binary",
                zero_division=0
            )
        )

        accuracy = accuracy_score(
            true_labels,
            predicted_labels
        )

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }

    return compute_pdf_metrics

def train_model():
    train_raw = load_split(TRAIN_PATH)
    validation_raw = load_split(VALIDATION_PATH)

    if len(train_raw) == 0:
        raise ValueError("No training PDFs with extractable text were found.")

    if len(validation_raw) == 0:
        raise ValueError("No validation PDFs with extractable text were found.")

    train_dataset, _ = prepare_dataset(train_raw)

    validation_dataset, validation_pdf_ids = prepare_dataset(validation_raw)
    model = create_model()

    training_args = TrainingArguments(
        output_dir="./lexical_training",
        num_train_epochs=5,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        learning_rate=5e-5,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=10,
        load_best_model_at_end=True,
        metric_for_best_model="eval_f1",
        greater_is_better=True,
        use_cpu=True
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        compute_metrics=create_pdf_metrics(validation_pdf_ids)
    )

    trainer.train()

    trainer.save_model(MODEL_OUTPUT_PATH)
    get_training_tokeniser().save_pretrained(MODEL_OUTPUT_PATH)

    get_inference_model.cache_clear()
    get_inference_tokeniser.cache_clear()

    return trainer

def lexical_ai_probability(text, max_chunks=None):
    text = (text or "").strip()

    if not text:
        return 0.5

    model = get_inference_model()
    inference_tokeniser = get_inference_tokeniser()

    encoded = inference_tokeniser(
        text,
        truncation=True,
        max_length=MAX_LENGTH,
        return_overflowing_tokens=True,
        padding="max_length",
        return_tensors="pt"
    )

    input_ids = encoded["input_ids"]
    attention_mask = encoded["attention_mask"]

    ai_scores = []

    if max_chunks is not None:
        input_ids = input_ids[:max_chunks]
        attention_mask = attention_mask[:max_chunks]

    with torch.no_grad():
        for start in range(0, len(input_ids), INFERENCE_BATCH_SIZE):
            end = start + INFERENCE_BATCH_SIZE
            batch_input_ids = input_ids[start:end]
            batch_attention_mask = attention_mask[start:end]


            outputs = model(
                input_ids=batch_input_ids,
                attention_mask=batch_attention_mask
            )

            probabilities = torch.softmax(
                outputs.logits,
                dim=-1
            )

            batch_ai_scores = probabilities[:, 1]
            ai_scores.extend(batch_ai_scores.tolist())

    if not ai_scores:
        return 0.5
    
    return float(np.mean(ai_scores))

if __name__ == "__main__":
    test_model_pdf_level()