"""
complaint_adapter.py — Integration adapter between Member 3's TF-IDF
matching engine (src/analysis/matching_engine.py) and Member 4's
Streamlit app, which expects analyze_complaint(text) -> dict in the shape:

    {
        "obd_code": <full OBD_Codes row dict, or None>,
        "confidence": float in [0, 1],
        "matched_keywords": [str, ...],
        "additional_matches": [
            {"fault_name": str, "obd_code": str, "similarity_score": float, "confidence": str},
            ...
        ],
    }

Member 3's engine returns a different shape (status flag, OBD code as a
bare string, confidence as a High/Medium/Low label, a similarity_score
float, plus repair-knowledge fields). Rather than changing either side's
contract, this module translates between them so app.py's rendering
code (written against Member 4's original keyword engine) keeps working
unmodified.

Do not edit matching_engine.py or text_preprocessor.py to "fix" this —
edit this file instead.
"""

from src.analysis.matching_engine import analyze_complaint as _tfidf_analyze
from src.analysis.text_preprocessor import preprocess
from src.db import get_obd_code


def _extract_matched_keywords(complaint_text, matched_complaint_text):
    """
    The TF-IDF engine doesn't return matched keywords directly (it's a
    similarity score over the full text, not a keyword-overlap score).
    For UI purposes (app.py shows "Matched keywords: ..."), approximate
    this as the overlap between the preprocessed complaint tokens and
    the preprocessed tokens of the training complaint that matched best.
    """
    complaint_tokens = set(preprocess(complaint_text or "").split())
    matched_tokens = set(preprocess(matched_complaint_text or "").split())
    return sorted(complaint_tokens & matched_tokens)


def analyze_complaint(complaint_text):
    """
    Drop-in replacement for the old src.analysis_engine.analyze_complaint,
    backed by Member 3's TF-IDF engine.
    """
    result = _tfidf_analyze(complaint_text)

    status = result.get("status")

    if status in ("error", "no_match"):
        return {
            "obd_code": None,
            "confidence": result.get("similarity_score", 0.0) or 0.0,
            "matched_keywords": [],
            "additional_matches": [],
        }

    # status == "success"
    obd_code_str = result.get("obd_code")
    full_obd_row = get_obd_code(obd_code_str) if obd_code_str else None

    matched_keywords = _extract_matched_keywords(
        complaint_text, result.get("matched_complaint")
    )

    return {
        "obd_code": full_obd_row,
        "confidence": result.get("similarity_score", 0.0) or 0.0,
        "matched_keywords": matched_keywords,
        "additional_matches": result.get("additional_matches", []),
    }