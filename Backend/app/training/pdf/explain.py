import argparse
import numpy as np
import torch
from functools import lru_cache
from app.training.pdf.features import extract_pdf_features
from app.training.pdf.lexical import extract_pdf_text, lexical_ai_probability

from app.training.pdf.model import PDFDetector

def encode_sequence(sequence, vocab, max_length):
    encoded = [
        vocab.get(token, vocab["<UNK>"])
        for token in sequence[:max_length]
    ]

    return (encoded + [vocab["<PAD>"]] * (max_length - len(encoded)))

@lru_cache
def load_detector(model_path):
    checkpoint = torch.load(
        model_path,
        map_location="cpu",
        weights_only=False
    )

    model = PDFDetector(
        object_vocab_size=len(checkpoint["object_vocab"]),
        object_pad_id=checkpoint["object_vocab"]["<PAD>"],
        font_vocab_size=len(checkpoint["font_vocab"]),
        font_pad_id=checkpoint["font_vocab"]["<PAD>"],
        line_basic_dim=(len(checkpoint["basic_keys"]) + len(checkpoint["line_keys"])),
        font_numeric_dim=len(checkpoint["font_keys"]),
        object_numeric_dim=len(checkpoint["object_keys"])
    )

    model.load_state_dict(checkpoint["model_state"])

    model.eval()
    return model, checkpoint

def prepare_inputs(pdf_path, checkpoint):
    features = extract_pdf_features(pdf_path)
    text = extract_pdf_text(pdf_path)
    lexical_score = lexical_ai_probability(text)

    object_vocab = checkpoint["object_vocab"]
    font_vocab = checkpoint["font_vocab"]

    object_ids = encode_sequence(
        features["object_sequence"],
        object_vocab,
        checkpoint["max_objects"]
    )

    font_ids = encode_sequence(
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
            float(
                features["line_features"].get(key, 0)
            ) for key in checkpoint["line_keys"]
        ], dtype=np.float32
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
            float(
                features["object_features"].get(key,0)
            )
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
            float(
                features["font_features"].get(key, 0)
            )
            for key in checkpoint["font_keys"]
        ], dtype=np.float32
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

    tensors = {
        "lexical": torch.tensor(
            [[lexical_score]],
            dtype=torch.float32
        ),

        "object_ids": torch.tensor(
            [object_ids],
            dtype=torch.long
        ),

        "object_numeric": torch.tensor(
            object_numeric[None, :],
            dtype=torch.float32
        ),

        "line_basic": torch.tensor(
            line_basic[None, :],
            dtype=torch.float32
        ),

        "font_ids": torch.tensor(
            [font_ids],
            dtype=torch.long
        ),

        "font_numeric": torch.tensor(
            font_numeric[None, :],
            dtype=torch.float32
        )
    }

    return features, lexical_score, tensors

def predict_probability(model, tensors):
    with torch.no_grad():
        logit = model(
            tensors["lexical"],
            tensors["object_ids"],
            tensors["object_numeric"],
            tensors["line_basic"],
            tensors["font_ids"],
            tensors["font_numeric"]
        )

        probability = torch.sigmoid(logit).item()

    return float(probability)

def neutralise_branch(tensors, branch, checkpoint):
    modified = {
        key: value.clone()
        for key, value in tensors.items()
    }

    if branch == "lexical":
        modified["lexical"][:] = 0.5

    elif branch == "object_sequence":
        pad_id = checkpoint["object_vocab"]["<PAD>"]
        unk_id = checkpoint["object_vocab"]["<UNK>"]

        modified["object_ids"][:] = pad_id
        modified["object_ids"][:, 0] = unk_id

    elif branch == "object_numeric":
        modified["object_numeric"].zero_()

    elif branch == "line_basic":
        modified["line_basic"].zero_()

    elif branch == "fonts":
        modified["font_ids"][:] = (
            checkpoint["font_vocab"]["<PAD>"]
        )

        modified["font_numeric"].zero_()

    return modified

def calculate_branch_contributions(model, tensors, checkpoint, full_probability):
    branches = [
        "lexical",
        "object_sequence",
        "object_numeric",
        "line_basic",
        "fonts"
    ]

    contributions = {}

    for branch in branches:
        modified = neutralise_branch(
            tensors,
            branch,
            checkpoint
        )

        probability_without_branch = (
            predict_probability(
                model,
                modified
            )
        )

        contribution = full_probability - probability_without_branch
        contributions[branch] = contribution

    return contributions

def contribution_strength(contribution):
    magnitude = abs(contribution)

    if magnitude >= 0.15:
        return "high"

    if magnitude >= 0.05:
        return "medium"

    return "low"

def contribution_direction(contribution):
    if contribution > 0:
        return "AI-generated content"

    if contribution < 0:
        return "authentic content"

    return "neither classification"

def branch_display_name(branch):
    names = {
        "lexical": "lexical analysis",
        "object_sequence": "PDF object sequence",
        "object_numeric": "PDF object structure",
        "line_basic": "line-ending and basic PDF structure",
        "fonts": "font analysis"
    }   

    return names.get(branch, branch)

def contribution_sentence(branch, contribution):
    strength = contribution_strength(contribution)
    direction = contribution_direction(contribution)
    name = branch_display_name(branch)

    if abs(contribution) < 1e-6:
        return (f"The {name} provides low evidence and does not clearly favour either classification.")

    return (f"The {name} provides {strength} evidence in favour of {direction}.")

def create_summary(prediction, probability, contributions):
    sorted_contributions = sorted(
        contributions.items(),
        key=lambda item: abs(item[1]),
        reverse=True
    )

    strongest_branch, strongest_value = (sorted_contributions[0])
    strongest_name = branch_display_name(strongest_branch)
    strongest_strength = (contribution_strength(strongest_value))

    strongest_direction = (contribution_direction(strongest_value))

    confidence = probability

    if prediction == "Authentic":
        confidence = 1.0 - probability

    if confidence >= 0.80:
        confidence_text = "high"
    elif confidence >= 0.60:
        confidence_text = "medium"
    else:
        confidence_text = "low"

    return (
        f"The document was classified as {prediction} "
        f"with {confidence_text} confidence. "
        f"The strongest evidence came from the "
        f"{strongest_name}, which provided "
        f"{strongest_strength} evidence in favour of "
        f"{strongest_direction}."
    )

def explain_pdf(pdf_path,model_path="app/ai/pdf_detector.pt"):
    model, checkpoint = load_detector(model_path)

    features, lexical_score, tensors = prepare_inputs(pdf_path, checkpoint)

    full_probability = predict_probability(model, tensors)

    contributions = (
        calculate_branch_contributions(
            model,
            tensors,
            checkpoint,
            full_probability
        )
    )

    prediction = "AI-generated" if full_probability >= 0.5 else "Authentic"

    sorted_contributions = sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)

    sentences = [
        contribution_sentence(
            branch,
            contribution
        )
        for branch, contribution
        in sorted_contributions
    ]

    summary = create_summary(
        prediction,
        full_probability,
        contributions
    )

    return {
        "prediction": prediction,
        "ai_probability": full_probability,
        "lexical_ai_probability": lexical_score,
        "summary": summary,
        "explanations": sentences,
        "branch_contributions": {
            branch: contribution
            for branch, contribution
            in sorted_contributions
        }
    }

def print_explanation(explanation):
    print(f"Prediction: {explanation['prediction']}")
    print(f"AI probability: {explanation['ai_probability']:.2%}")
    print(f"Lexical AI probability: {explanation['lexical_ai_probability']:.2%}")
    print("\nSummary:")
    print(explanation["summary"])

    print("\nExplanation:")

    for sentence in explanation["explanations"]:
        print(
            f"- {sentence}"
        )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument(
        "--model",
        default="app/ai/pdf_detector.pt"
    )

    args = parser.parse_args()
    explanation = explain_pdf(args.pdf, args.model)
    print_explanation(explanation)

if __name__ == "__main__":
    main()

