import re
import string
import nltk
from nltk.stem import WordNetLemmatizer


_FALLBACK_STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of",
    "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "in", "out",
    "on", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "both", "each", "few", "more",
    "most", "other", "some", "such", "than", "too", "same", "so", "just",
    "should", "now", "only", "own", "will", "would", "could", "might", "must",
    "can", "shall", "may", "need", "dare", "ought", "used",
}


# ---------------------------------------------------------
# NLTK RESOURCE SETUP
# ---------------------------------------------------------

_NLTK_RESOURCES = {
    "punkt": "tokenizers/punkt",
    "punkt_tab": "tokenizers/punkt_tab",
    "stopwords": "corpora/stopwords",
    "wordnet": "corpora/wordnet",
    "omw-1.4": "corpora/omw-1.4",
}


for resource, resource_path in _NLTK_RESOURCES.items():
    try:
        nltk.data.find(resource_path)
    except (LookupError, OSError):
        try:
            nltk.download(
                resource,
                quiet=True,
                raise_on_error=False
            )
        except Exception:
            pass


_nltk_available = {
    "tokenize": False,
    "stopwords": False,
    "lemmatize": False,
}


# ---------------------------------------------------------
# TOKENIZER SETUP
# ---------------------------------------------------------

try:
    from nltk.tokenize import word_tokenize as _nltk_tokenize

    _nltk_tokenize("test sentence")

    _nltk_available["tokenize"] = True

except Exception:
    _nltk_available["tokenize"] = False


# ---------------------------------------------------------
# STOPWORDS SETUP
# ---------------------------------------------------------

try:
    from nltk.corpus import stopwords as _nltk_stopwords

    _sw_set = set(
        _nltk_stopwords.words("english")
    )

    _nltk_available["stopwords"] = True

except Exception:
    _sw_set = _FALLBACK_STOPWORDS


# ---------------------------------------------------------
# LEMMATIZER SETUP
# ---------------------------------------------------------

_lemmatizer = None

try:
    _lemmatizer = WordNetLemmatizer()

    _lemmatizer.lemmatize("test")

    _nltk_available["lemmatize"] = True

except Exception:
    _nltk_available["lemmatize"] = False


_stopwords = (
    _sw_set
    if _nltk_available["stopwords"]
    else _FALLBACK_STOPWORDS
)


KEEP_WORDS = {
    "not",
    "no",
    "nor",
    "never",
    "without",
    "against",
    "up",
    "down",
    "very",
    "hard",
    "heavy",
    "low",
    "high",
}


_stopwords = _stopwords - KEEP_WORDS


# ---------------------------------------------------------
# AUTOMOTIVE NORMALIZATIONS
# ---------------------------------------------------------

AUTOMOTIVE_NORMALIZATIONS = {
    r"\bac\b": "air conditioning",
    r"\ba/c\b": "air conditioning",
    r"\beng\b": "engine",
    r"\btrans\b": "transmission",
    r"\bauto\b": "automatic",
    r"\babs\b": "antilock braking system",
    r"\becu\b": "engine control unit",
    r"\bobd\b": "onboard diagnostic",
    r"\brpm\b": "revolutions per minute",
    r"\bkmph\b": "kilometers per hour",
    r"\bkm\b": "kilometer",
    r"\bkmpl\b": "kilometers per liter",
    r"\bmpg\b": "miles per gallon",
    r"\bbrk\b": "brake",
    r"\bsteer\b": "steering",
    r"\bsusp\b": "suspension",
    r"\bcv\b": "constant velocity",
    r"\bvvt\b": "variable valve timing",
    r"\begr\b": "exhaust gas recirculation",
    r"\bmap\b": "manifold absolute pressure",
    r"\bmaf\b": "mass air flow",
    r"\btps\b": "throttle position sensor",
    r"\biat\b": "intake air temperature",
    r"\bect\b": "engine coolant temperature",
    r"\bclt\b": "coolant temperature",
    r"\bo2\b": "oxygen",
    r"\blambda\b": "oxygen sensor",
    r"\bdpf\b": "diesel particulate filter",
    r"\bcat\b": "catalytic converter",
    r"\bturbo\b": "turbocharger",
    r"\bsuv\b": "sport utility vehicle",
    r"\bfwd\b": "front wheel drive",
    r"\bawd\b": "all wheel drive",
    r"\b4wd\b": "four wheel drive",
    r"\brwd\b": "rear wheel drive",
    r"\batf\b": "automatic transmission fluid",
}


def _normalize_automotive_terms(text: str) -> str:

    for pattern, replacement in AUTOMOTIVE_NORMALIZATIONS.items():

        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE,
        )

    return text


def _remove_special_characters(text: str) -> str:

    text = re.sub(
        r"[^a-zA-Z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


# ---------------------------------------------------------
# MAIN PREPROCESS FUNCTION
# ---------------------------------------------------------

def preprocess(text: str) -> str:

    if not isinstance(text, str) or not text.strip():
        return ""

    text = text.lower()

    text = _normalize_automotive_terms(text)

    text = _remove_special_characters(text)


    if _nltk_available["tokenize"]:

        try:
            tokens = _nltk_tokenize(text)

        except Exception:
            tokens = text.split()

    else:

        tokens = text.split()


    tokens = [
        token
        for token in tokens
        if token not in string.punctuation
    ]


    tokens = [
        token
        for token in tokens
        if token not in _stopwords
    ]


    tokens = [
        token
        for token in tokens
        if len(token) > 1
    ]


    if (
        _nltk_available["lemmatize"]
        and _lemmatizer is not None
    ):

        try:

            tokens = [
                _lemmatizer.lemmatize(token)
                for token in tokens
            ]

            tokens = [
                _lemmatizer.lemmatize(
                    token,
                    pos="v",
                )
                for token in tokens
            ]

        except Exception:
            pass


    return " ".join(tokens)


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    sample_complaints = [

        "My car engine is getting extremely hot after driving for 20 minutes",

        "ABS warning light is on and brakes feel spongy",

        "AC is blowing warm air and not cooling the cabin",

        "Transmission slipping between gears when driving on highway",

        "Battery keeps dying overnight and car won't start in the morning",

    ]


    print(
        "Text Preprocessing Demo\n"
        + "=" * 50
    )


    for complaint in sample_complaints:

        processed = preprocess(complaint)

        print(
            f"Original : {complaint}"
        )

        print(
            f"Processed: {processed}"
        )

        print("-" * 50)