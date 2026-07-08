import os
import sys
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.analysis.text_preprocessor import preprocess
from src.analysis.complaint_dataset import generate_complaint_dataset, OUTPUT_PATH

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_REPAIR_KNOWLEDGE_PATH = os.path.join(_BASE_DIR, "data", "processed", "repair_knowledge.csv")

HELD_OUT_FRACTION = 0.10
RANDOM_SEED = 42


def _build_model(train_df: pd.DataFrame):
    train_df["processed_text"] = train_df["complaint_text"].apply(preprocess)
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.85,
        sublinear_tf=True,
        smooth_idf=True,
    )
    matrix = vectorizer.fit_transform(train_df["processed_text"])
    return vectorizer, matrix, train_df


def _predict(query: str, vectorizer, matrix, train_df: pd.DataFrame) -> dict:
    processed = preprocess(query)
    vec = vectorizer.transform([processed])
    scores = cosine_similarity(vec, matrix).flatten()
    best_idx = int(np.argmax(scores))
    return {
        "predicted_fault": train_df.iloc[best_idx]["fault_name"],
        "score": float(scores[best_idx]),
    }


def run_evaluation():
    if not os.path.exists(OUTPUT_PATH):
        print("Complaint dataset not found – generating now...")
        generate_complaint_dataset()

    df = pd.read_csv(OUTPUT_PATH, encoding="utf-8")

    train_df, test_df = train_test_split(
        df,
        test_size=HELD_OUT_FRACTION,
        stratify=df["fault_name"],
        random_state=RANDOM_SEED,
    )

    vectorizer, matrix, train_df_indexed = _build_model(train_df.reset_index(drop=True))

    correct = 0
    total = len(test_df)
    all_scores = []
    results = []

    for _, row in test_df.iterrows():
        prediction = _predict(row["complaint_text"], vectorizer, matrix, train_df_indexed)
        is_correct = prediction["predicted_fault"] == row["fault_name"]
        correct += int(is_correct)
        all_scores.append(prediction["score"])
        results.append({
            "complaint": row["complaint_text"][:60] + "..." if len(row["complaint_text"]) > 60 else row["complaint_text"],
            "true_fault": row["fault_name"],
            "predicted_fault": prediction["predicted_fault"],
            "similarity_score": round(prediction["score"], 4),
            "correct": "YES" if is_correct else "NO",
        })

    accuracy = correct / total
    avg_score = float(np.mean(all_scores))

    print("\n" + "=" * 70)
    print("COMPLAINT ANALYSIS ENGINE – EVALUATION REPORT")
    print("=" * 70)
    print(f"Train samples : {len(train_df)}")
    print(f"Test samples  : {total}")
    print(f"Top-1 Accuracy: {accuracy:.2%}  ({correct}/{total} correct)")
    print(f"Avg Similarity: {avg_score:.4f}")
    print("=" * 70)

    results_df = pd.DataFrame(results)
    print("\nDetailed Results:")
    print(results_df.to_string(index=False))

    fault_accuracy = (
        pd.DataFrame(results)
        .assign(correct_bool=lambda x: x["correct"] == "YES")
        .groupby("true_fault")["correct_bool"]
        .agg(["sum", "count"])
        .rename(columns={"sum": "correct", "count": "total"})
    )
    fault_accuracy["accuracy"] = (fault_accuracy["correct"] / fault_accuracy["total"]).map("{:.0%}".format)
    print("\nPer-Fault Accuracy:")
    print(fault_accuracy.to_string())
    print("=" * 70)

    if accuracy >= 0.70:
        print("\nRESULT: Engine meets the 70% accuracy threshold. Ready for integration.")
    else:
        print(f"\nRESULT: Accuracy {accuracy:.2%} is below 70% threshold. Review corpus or preprocessing.")

    return accuracy, avg_score


if __name__ == "__main__":
    run_evaluation()
