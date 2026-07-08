import os
import sys
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.analysis.text_preprocessor import preprocess

USE_SENTENCE_TRANSFORMERS = False

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_COMPLAINT_DATASET_PATH = os.path.join(_BASE_DIR, "data", "knowledge", "complaint_dataset.csv")
_REPAIR_KNOWLEDGE_PATH = os.path.join(_BASE_DIR, "data", "processed", "repair_knowledge.csv")

_SIMILARITY_THRESHOLDS = {
    "high": 0.45,
    "medium": 0.25,
    "low": 0.15,
}

_corpus_df: pd.DataFrame = None
_repair_df: pd.DataFrame = None
_tfidf_vectorizer: TfidfVectorizer = None
_tfidf_matrix: np.ndarray = None
_is_initialized: bool = False


def _load_and_build_index():
    global _corpus_df, _repair_df, _tfidf_vectorizer, _tfidf_matrix, _is_initialized

    _corpus_df = pd.read_csv(_COMPLAINT_DATASET_PATH, encoding="utf-8")
    _repair_df = pd.read_csv(_REPAIR_KNOWLEDGE_PATH, encoding="utf-8")

    _repair_df.rename(columns=lambda c: c.strip(), inplace=True)
    _corpus_df["processed_text"] = _corpus_df["complaint_text"].apply(preprocess)

    _tfidf_vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.85,
        sublinear_tf=True,
        smooth_idf=True,
    )
    _tfidf_matrix = _tfidf_vectorizer.fit_transform(_corpus_df["processed_text"])
    _is_initialized = True


def _ensure_initialized():
    if not _is_initialized:
        _load_and_build_index()


def _get_confidence_label(score: float) -> str:
    if score >= _SIMILARITY_THRESHOLDS["high"]:
        return "High"
    if score >= _SIMILARITY_THRESHOLDS["medium"]:
        return "Medium"
    if score >= _SIMILARITY_THRESHOLDS["low"]:
        return "Low"
    return "No Match"


def _enrich_with_repair_knowledge(fault_obd_code: str) -> dict:
    if _repair_df is None or fault_obd_code is None:
        return {}

    match = _repair_df[_repair_df["OBD_Code"] == fault_obd_code]
    if match.empty:
        return {}

    row = match.iloc[0]
    return {
        "description": row.get("Description", ""),
        "cause": row.get("Cause", ""),
        "solution": row.get("Solution", ""),
        "estimated_cost_inr": row.get("Estimated_Cost_INR", ""),
        "repair_time": row.get("Repair_Time", ""),
        "severity": row.get("Severity", ""),
        "preventive_maintenance": row.get("Preventive_Maintenance", ""),
    }


def analyze_complaint(complaint_text: str, top_n: int = 1) -> dict:
    _ensure_initialized()

    if not isinstance(complaint_text, str) or not complaint_text.strip():
        return {
            "status": "error",
            "message": "Complaint text is empty or invalid.",
        }

    processed_query = preprocess(complaint_text)

    if not processed_query.strip():
        return {
            "status": "error",
            "message": "Complaint text could not be processed after cleaning.",
        }

    query_vector = _tfidf_vectorizer.transform([processed_query])
    similarity_scores = cosine_similarity(query_vector, _tfidf_matrix).flatten()

    best_idx = int(np.argmax(similarity_scores))
    best_score = float(similarity_scores[best_idx])
    confidence = _get_confidence_label(best_score)

    if confidence == "No Match":
        return {
            "status": "no_match",
            "message": "Could not identify a matching fault. Please provide more specific details about the vehicle problem.",
            "similarity_score": round(best_score, 4),
            "confidence": confidence,
        }

    best_row = _corpus_df.iloc[best_idx]
    repair_info = _enrich_with_repair_knowledge(best_row["obd_code"])

    result = {
        "status": "success",
        "fault_name": best_row["fault_name"],
        "obd_code": best_row["obd_code"],
        "fault_category": best_row["fault_category"],
        "matched_complaint": best_row["complaint_text"],
        "similarity_score": round(best_score, 4),
        "confidence": confidence,
    }
    result.update(repair_info)

    return result


def get_top_matches(complaint_text: str, top_n: int = 5) -> list:
    _ensure_initialized()

    if not isinstance(complaint_text, str) or not complaint_text.strip():
        return []

    processed_query = preprocess(complaint_text)
    query_vector = _tfidf_vectorizer.transform([processed_query])
    similarity_scores = cosine_similarity(query_vector, _tfidf_matrix).flatten()

    top_indices = np.argsort(similarity_scores)[::-1][:top_n]
    results = []

    for idx in top_indices:
        row = _corpus_df.iloc[idx]
        score = float(similarity_scores[idx])
        results.append({
            "rank": len(results) + 1,
            "fault_name": row["fault_name"],
            "obd_code": row["obd_code"],
            "fault_category": row["fault_category"],
            "matched_complaint": row["complaint_text"],
            "similarity_score": round(score, 4),
            "confidence": _get_confidence_label(score),
        })

    return results


if __name__ == "__main__":
    test_complaints = [
        "Car engine getting very hot and steam from hood",
        "Battery keeps dying and car won't start",
        "Brakes are squealing and pedal feels soft",
        "Transmission is slipping between gears",
        "AC blowing hot air in the cabin",
    ]

    print("Matching Engine – Quick Test\n" + "=" * 60)
    for complaint in test_complaints:
        result = analyze_complaint(complaint)
        print(f"Complaint : {complaint}")
        if result["status"] == "success":
            print(f"Fault     : {result['fault_name']} ({result['obd_code']})")
            print(f"Score     : {result['similarity_score']} [{result['confidence']}]")
            print(f"Severity  : {result.get('severity', 'N/A')}")
            print(f"Cost (INR): {result.get('estimated_cost_inr', 'N/A')}")
        else:
            print(f"Status    : {result['status']} – {result['message']}")
        print("-" * 60)
