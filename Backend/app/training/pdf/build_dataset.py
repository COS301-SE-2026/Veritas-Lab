import argparse, json
from pathlib import Path
from tqdm import tqdm
from app.training.pdf.features import extract_pdf_features
from app.training.pdf.lexical import lexical_ai_probability, extract_pdf_text

def pdfs(folder):
    return sorted(Path(folder).rglob("*.pdf"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ai-dir", required=True)
    parser.add_argument("--authentic-dir", required=True)
    parser.add_argument("--output", default="features.jsonl")
    parser.add_argument("--skip-lexical", action="store_true")

    args = parser.parse_args()

    jobs = ([(path, 1) for path in pdfs(args.ai_dir)] + [(path, 0) for path in pdfs(args.authentic_dir)])

    print("Total PDFs:", len(jobs))

    with open(args.output, "w", encoding="utf-8") as out:
        for path, label in tqdm(jobs):
            try:
                row = extract_pdf_features(path)
                if args.skip_lexical:
                    lexical_probability = 0.5
                else:
                    text = extract_pdf_text(path)
                    lexical_probability = lexical_ai_probability(text)

                row["lexical_ai_probability"] = lexical_probability
                row["label"] = label

                out.write(
                    json.dumps(
                        row,
                        ensure_ascii=False
                    ) + "\n"
                )

            except Exception as e:
                print(f"FAILED: {path}: {e}")

if __name__ == "__main__":
    main()