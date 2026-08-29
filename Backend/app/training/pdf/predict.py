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
        weights_only=False
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

    line_basic = (
        line_basic
        - np.array(checkpoint["line_mean"], dtype=np.float32)
    ) / np.array(
        checkpoint["line_std"],
        dtype=np.float32
    )



if __name__ == "__main__":
    main()
