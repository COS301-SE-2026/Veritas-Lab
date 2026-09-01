import argparse, numpy as np, torch
from app.training.pdf.features import extract_pdf_features
from app.training.pdf.lexical import lexical_ai_probability, extract_pdf_text
from app.training.pdf.model import PDFDetector

def enc(seq, vocab, max_length):
    encoded = [
        vocab.get(token, vocab["<UNK>"])
        for token in seq[:max_length]
    ]

    return encoded + [vocab["<PAD>"]] * (max_length - len(encoded))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--model", default="pdf_detector.pt")
    parser.add_argument("--skip-lexical", action="store_true")

    args = parser.parse_args()

    checkpoint = torch.load(
        args.model,
        map_location="cpu",
        weights_only=True
    )

    features = extract_pdf_features(args.pdf)

    if args.skip_lexical:
        lexical_score = 0.5
    else:
        text = extract_pdf_text(args.pdf)
        lexical_score = lexical_ai_probability(text)

    object_vocab = checkpoint["object_vocab"]
    font_vocab = checkpoint["font_vocab"]

    object_ids = enc(
        features["object_sequence"],
        object_vocab,
        checkpoint["max_objects"]
    )

    font_ids = enc(
        features["font_tokens"],
        font_vocab,
        checkpoint["max_fonts"]
    )

    line_basic = np.array(
        [
            float(features.get(key, 0))
            for key in checkpoint["basic_keys"]
        ] +
        [
            float(features["line_features"].get(key, 0))
            for key in checkpoint["line_keys"]
        ],
        dtype=np.float32
    )

    line_mean = np.array(
        checkpoint["line_mean"],
        dtype=np.float32
    )

    line_std = np.array(
        checkpoint["line_std"],
        dtype=np.float32
    )

    line_basic = (line_basic - line_mean) / line_std

    object_numeric = np.array(
        [
            float(features["object_features"].get(key,0))
            for key in checkpoint["object_keys"]
        ], dtype=np.float32
    )

    object_mean = np.array(
        checkpoint["object_mean"],
        dtype=np.float32
    )

    object_std = np.array(
        checkpoint["object_std"],
        dtype=np.float32
    )

    object_numeric = (object_numeric - object_mean) / object_std

    font_numeric = np.array(
        [
            float(features["font_features"].get(key,0))
            for key in checkpoint ["font_keys"]
        ],
        dtype=np.float32
    )

    font_mean = np.array(
        checkpoint["font_mean"],
        dtype=np.float32
    )

    font_std = np.array(
        checkpoint["font_std"],
        dtype=np.float32
    )

    font_numeric = (font_numeric - font_mean) / font_std

    model = PDFDetector(
        object_vocab_size=len(object_vocab),
        object_pad_id=object_vocab["<PAD>"],
        font_vocab_size=len(font_vocab),
        font_pad_id=font_vocab["<PAD>"],
        line_basic_dim=len(line_basic),
        font_numeric_dim=len(font_numeric),
        object_numeric_dim=len(object_numeric)
    )

    model.load_state_dict(checkpoint["model_state"])

    model.eval()

    lexical_tensor = torch.tensor(
        [[lexical_score]],
        dtype=torch.float32
    )

    object_ids_tensor = torch.tensor(
        [object_ids],
        dtype=torch.long
    )

    object_numeric_tensor = torch.tensor(
        object_numeric[None, :],
        dtype=torch.float32
    )

    line_basic_tensor = torch.tensor(
        line_basic[None, :],
        dtype=torch.float32
    )

    font_ids_tensor = torch.tensor(
        [font_ids],
        dtype=torch.long
    )

    font_numeric_tensor = torch.tensor(
        font_numeric[None, :],
        dtype=torch.float32
    )

    with torch.no_grad():
        logit = model(
            lexical_tensor,
            object_ids_tensor,
            object_numeric_tensor,
            line_basic_tensor,
            font_ids_tensor,
            font_numeric_tensor
        )

        probability = float(torch.sigmoid(logit).item())

    print(f"Lexical AI score: {lexical_score:.4f}")
    print(f"Final AI probability: {probability:.4f}")
    print(
        "Prediction:",
        "AI-generated"
        if probability >= 0.5
        else "Authentic"
    )

if __name__ == "__main__":
    main()
