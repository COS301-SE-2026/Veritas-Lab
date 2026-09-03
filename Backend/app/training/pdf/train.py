import argparse
import json
import random
from collections import Counter

import numpy as np
import torch

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

from torch import nn
from torch.utils.data import Dataset, DataLoader
from app.training.pdf.model import PDFDetector

PAD = "<PAD>"
UNK = "<UNK>"

BASIC = [
    "page_count",
    "xref_object_count",
    "pdf_version",
    "file_size_kb",
    "xref_objects_per_page",
    "xref_objects_per_kb"
]

LINE = [
    "lf_count",
    "crlf_count",
    "cr_count",
    "lf_ratio",
    "crlf_ratio",
    "cr_ratio",
    "line_endings_per_kb",
    "classic_xref_count",
    "startxref_count",
    "eof_count"
]

OBJECT = [
    "object_count_analyzed",
    "page_object_ratio",
    "pages_object_ratio",
    "catalog_object_ratio",
    "font_object_ratio",
    "font_descriptor_ratio",
    "image_object_ratio",
    "xobject_ratio",
    "stream_object_ratio",
    "xref_stream_ratio",
    "object_stream_ratio",
    "filespec_ratio",
    "metadata_object_ratio",
    "info_object_ratio",
    "other_object_ratio",
    "unreadable_object_ratio",
    "unique_object_type_count"
]

FONT = [
    "font_reference_count",
    "unique_font_count",
    "embedded_font_count",
    "subset_font_reference_count",
    "base14_font_reference_count",
    "non_base14_ratio",
    "type0_count",
    "type1_count",
    "truetype_count",
    "font_references_per_page",
    "unique_fonts_per_page",
    "embedded_font_ratio",
    "subset_font_ratio"
]

def load_rows(path):
    with open(path, encoding="utf-8") as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]

def build_vocab(sequences):
    vocab = {
        PAD: 0,
        UNK: 1
    }

    counts = Counter(
        token
        for sequence in sequences
        for token in sequence
    )

    for token, _ in counts.most_common():
        vocab[token] = len(vocab)

    return vocab

def encode_sequence(sequence, vocab, max_length):
    encoded = [
        vocab.get(token, vocab[UNK])
        for token in sequence[:max_length]
    ]

    return encoded + [vocab[PAD]] * (max_length - len(encoded))

def calculate_stats(rows, keys, nested=None):
    values = np.array(
        [
            [
                float((row[nested] if nested else row).get(key, 0))
                for key in keys
            ]
            for row in rows
        ], dtype=np.float32
    )

    mean = values.mean(axis=0)
    std = values.std(axis=0)

    std[std < 1e-6] = 1.0

    return mean, std

class PDFDataset(Dataset):
    def __init__(
        self,
        rows,
        object_vocab,
        font_vocab,
        max_objects,
        max_fonts,
        line_mean,
        line_std,
        object_mean,
        object_std,
        font_mean,
        font_std
    ):
        self.rows = rows

        self.object_vocab = object_vocab
        self.font_vocab = font_vocab

        self.max_objects = max_objects
        self.max_fonts = max_fonts

        self.line_mean = line_mean
        self.line_std = line_std

        self.object_mean = object_mean
        self.object_std = object_std

        self.font_mean = font_mean
        self.font_std = font_std

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]

        lexical = np.array(
            [
                float(row["lexical_ai_probability"])
            ],
            dtype=np.float32
        )

        line_basic = np.array(
            [
                float(row.get(key, 0))
                for key in BASIC
            ] +

            [
                float(row["line_features"].get(key, 0))
                for key in LINE
            ],
            dtype=np.float32
        )

        line_basic = (line_basic - self.line_mean) / self.line_std

        object_numeric = np.array(
            [
                float(row["object_features"].get(key, 0))
                for key in OBJECT
            ],
            dtype=np.float32
        )

        object_numeric = (object_numeric - self.object_mean) / self.object_std

        font_numeric = np.array(
            [
                float(row["font_features"].get(key, 0))
                for key in FONT
            ],
            dtype=np.float32
        )

        font_numeric = (font_numeric - self.font_mean) / self.font_std

        object_ids = encode_sequence(
            row["object_sequence"],
            self.object_vocab,
            self.max_objects
        )

        font_ids = encode_sequence(
            row["font_tokens"],
            self.font_vocab,
            self.max_fonts
        )

        return {
            "lex": torch.from_numpy(lexical),

            "obj": torch.tensor(
                object_ids,
                dtype=torch.long
            ),

            "objnum": torch.from_numpy(object_numeric),

            "line": torch.from_numpy(line_basic),

            "fonts": torch.tensor(
                font_ids,
                dtype=torch.long
            ),

            "fontnum": torch.from_numpy(font_numeric),

            "y": torch.tensor(
                float(row["label"]),
                dtype=torch.float32
            )
        }

def evaluate_model(model, loader, device):
    true_labels = []
    probabilities = []
    model.eval()

    with torch.no_grad():
        for batch in loader:
            logits = model(
                batch["lex"].to(device),
                batch["obj"].to(device),
                batch["objnum"].to(device),
                batch["line"].to(device),
                batch["fonts"].to(device),
                batch["fontnum"].to(device)
            )

            batch_probabilities = torch.sigmoid(logits)

            probabilities.extend(batch_probabilities.cpu().tolist())

            true_labels.extend(batch["y"].tolist())

    predictions = [
        int(probability >= 0.5)
        for probability in probabilities
    ]

    return (
        true_labels,
        predictions,
        probabilities
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--train-features",
        required=True
    )

    parser.add_argument(
        "--validation-features",
        required=True
    )

    parser.add_argument(
        "--output",
        default="pdf_detector.pt"
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=25
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=16
    )

    parser.add_argument(
        "--lr",
        type=float,
        default=3e-4
    )

    parser.add_argument(
        "--max-objects",
        type=int,
        default=256
    )

    parser.add_argument(
        "--max-fonts",
        type=int,
        default=64
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42
    )

    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    train_rows = load_rows(args.train_features)

    validation_rows = load_rows(args.validation_features)

    print(f"Training PDFs: {len(train_rows)}")

    print(f"Validation PDFs: {len(validation_rows)}")

    object_vocab = build_vocab(
        [
            row["object_sequence"]
            for row in train_rows
        ]
    )

    font_vocab = build_vocab(
        [
            row["font_tokens"]
            for row in train_rows
        ]
    )

    line_rows = [
        {
            **{
                key: row.get(key, 0)
                for key in BASIC
            },
            **row["line_features"]
        }
        for row in train_rows
    ]

    line_mean, line_std = calculate_stats(
        line_rows,
        BASIC + LINE
    )

    object_mean, object_std = calculate_stats(
        train_rows,
        OBJECT,
        "object_features"
    )

    font_mean, font_std = calculate_stats(
        train_rows,
        FONT,
        "font_features"
    )

    train_dataset = PDFDataset(
        train_rows,
        object_vocab,
        font_vocab,
        args.max_objects,
        args.max_fonts,
        line_mean,
        line_std,
        object_mean,
        object_std,
        font_mean,
        font_std
    )

    validation_dataset = PDFDataset(
        validation_rows,
        object_vocab,
        font_vocab,
        args.max_objects,
        args.max_fonts,
        line_mean,
        line_std,
        object_mean,
        object_std,
        font_mean,
        font_std
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=args.batch_size
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("Device:", device)

    model = PDFDetector(
        object_vocab_size=len(object_vocab),
        object_pad_id=object_vocab[PAD],
        font_vocab_size=len(font_vocab),
        font_pad_id=font_vocab[PAD],
        line_basic_dim=len(BASIC) + len(LINE),
        font_numeric_dim=len(FONT),
        object_numeric_dim=len(OBJECT)
    ).to(device)

    positive_count = sum(
        row["label"] == 1
        for row in train_rows
    )

    negative_count = len(train_rows) - positive_count

    positive_weight = negative_count / max(positive_count, 1)

    loss_function = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor(
            [positive_weight],
            device=device
        )
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=1e-4
    )

    best_accuracy = -1.0
    best_state = None

    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []

        for batch in train_loader:
            optimizer.zero_grad(set_to_none=True)

            logits = model(
                batch["lex"].to(device),
                batch["obj"].to(device),
                batch["objnum"].to(device),
                batch["line"].to(device),
                batch["fonts"].to(device),
                batch["fontnum"].to(device)
            )

            loss = loss_function(logits, batch["y"].to(device))

            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

            optimizer.step()
            losses.append(loss.item())


        (true_labels, predictions, _) = evaluate_model(
            model,
            validation_loader,
            device
        )

        accuracy = accuracy_score(true_labels, predictions)

        print(f"Epoch {epoch:02d} loss={np.mean(losses):.4f} val_acc={accuracy:.4f}")

        if accuracy > best_accuracy:
            best_accuracy = accuracy

            best_state = {
                key: value.detach().cpu().clone()
                for key, value
                in model.state_dict().items()
            }

    model.load_state_dict(best_state)

    (true_labels, predictions, _) = evaluate_model(
        model,
        validation_loader,
        device
    )

    print(
        confusion_matrix(
            true_labels,
            predictions
        )
    )

    print(
        classification_report(
            true_labels,
            predictions,
            target_names=[
                "authentic",
                "AI"
            ],
            digits=4
        )
    )

    checkpoint = {
        "model_state": model.state_dict(),
        "object_vocab": object_vocab,
        "font_vocab": font_vocab,
        "max_objects": args.max_objects,
        "max_fonts": args.max_fonts,
        "basic_keys": BASIC,
        "line_keys": LINE,
        "object_keys": OBJECT,
        "font_keys": FONT,
        "line_mean": line_mean.tolist(),
        "line_std": line_std.tolist(),
        "object_mean": object_mean.tolist(),
        "object_std": object_std.tolist(),
        "font_mean": font_mean.tolist(),
        "font_std": font_std.tolist(),
        "best_validation_accuracy": best_accuracy
    }

    torch.save(checkpoint,args.output)
    print("Saved:",args.output)


if __name__ == "__main__":
    main()
