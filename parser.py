"""
parser.py

Provides a heuristic ingredient extractor. This is intentionally simple:
- It looks for measurement tokens (cup, tbsp, tsp, g, kg, oz, slice, pinch) and
  numeric quantities, or common ingredient keywords.
- For better accuracy, integration with OpenAI or spaCy could be added.
"""
import re

# A small list of common cooking measurement words and common ingredient tokens
MEASURE_WORDS = [
    "cup",
    "cups",
    "tbsp",
    "tablespoon",
    "tablespoons",
    "tsp",
    "teaspoon",
    "teaspoons",
    "g",
    "kg",
    "oz",
    "lb",
    "ml",
    "pinch",
    "slice",
]

COMMON_INGREDIENTS = [
    "salt",
    "pepper",
    "sugar",
    "flour",
    "egg",
    "eggs",
    "milk",
    "butter",
    "oil",
    "olive oil",
    "garlic",
    "onion",
    "tomato",
    "cheese",
    "basil",
    "parsley",
    "cilantro",
    "chicken",
    "beef",
    "pork",
    "rice",
    "water",
]


def extract_ingredients(text, max_items=30):
    """Return a list of guessed ingredients from `text`.

    This is a heuristic, rule-based extractor. It returns a de-duplicated list
    of candidate ingredient phrases.
    """
    if not text:
        return []

    text = text.replace("\n", " ")
    candidates = []

    # 1) Find phrases with a quantity/measure, e.g. '2 cups of flour', '1 tbsp sugar'
    qty_pattern = re.compile(r"(\d+\s?\/?\d*\s*(?:%s)\s+(?:of\s+)?[A-Za-z][A-Za-z \-()]+)" % "|".join(MEASURE_WORDS), re.IGNORECASE)
    for m in qty_pattern.findall(text):
        candidates.append(m.strip())

    # 2) Find short phrases that contain common ingredient keywords
    for ing in COMMON_INGREDIENTS:
        pattern = re.compile(r"([A-Za-z \-]{0,30}%s[A-Za-z \-]{0,30})" % re.escape(ing), re.IGNORECASE)
        for m in pattern.findall(text):
            candidates.append(m.strip())

    # 3) Split by commas and conjunctions and look for tokens that look like ingredients
    parts = re.split(r",|\band\b|\bwith\b|\bon\b", text, flags=re.IGNORECASE)
    short_token_pattern = re.compile(r"\b(?:%s)\b|\d+\s*(?:%s)\b" % ("|".join([re.escape(i) for i in COMMON_INGREDIENTS]), "|".join(MEASURE_WORDS)), re.IGNORECASE)
    for p in parts:
        if short_token_pattern.search(p):
            token = p.strip()
            # shorten long tokens
            if len(token) > 80:
                token = token[:80].rsplit(" ", 1)[0]
            candidates.append(token)

    # Normalize and dedupe while preserving order
    normalized = []
    seen = set()
    for c in candidates:
        s = re.sub(r"\s+", " ", c).strip().lower()
        if s and s not in seen:
            seen.add(s)
            normalized.append(s)
        if len(normalized) >= max_items:
            break

    return normalized
