"""
Keyword index for garment-dynamics.
Inverted index for intent decomposition and keyword search.
"""


STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can",
    "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "and", "or", "but", "not", "no", "so", "if", "then",
    "that", "this", "it", "its", "my", "your", "our",
    "very", "really", "just", "also", "too", "quite",
    "like", "want", "need", "looking", "something", "make",
    "garment", "clothing", "outfit", "dress", "wear", "wearing",
    "style", "styled", "fashion", "fashionable",
}

KEYWORD_CATEGORIES = {
    "mood": ["dramatic", "intimate", "powerful", "soft", "mysterious",
             "romantic", "edgy", "minimal", "bold", "ethereal",
             "commanding", "delicate", "tough", "playful", "elegant"],
    "era": ["victorian", "90s", "60s", "70s", "50s", "ancient",
            "classical", "modern", "futuristic", "vintage", "retro",
            "contemporary", "renaissance", "medieval"],
    "designer": ["margiela", "balenciaga", "valentino", "chanel",
                 "comme-des-garcons", "iris-van-herpen", "dvf",
                 "burberry", "alexander-mcqueen"],
    "occasion": ["bridal", "red-carpet", "street", "resort", "party",
                 "professional", "casual", "formal", "event", "editorial"],
    "silhouette": ["column", "a-line", "hourglass", "boxy", "fitted",
                   "flowing", "structured", "voluminous", "narrow",
                   "tapered", "flared", "asymmetric"],
    "fabric_mood": ["liquid", "crisp", "sculptural", "soft", "stiff",
                    "sheer", "heavy", "light", "textured", "smooth"],
}


def tokenize_intent(text: str) -> list:
    """Tokenize intent string, removing stop words."""
    tokens = text.lower().replace("-", " ").replace("_", " ").split()
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def build_keyword_index(garment_catalog: dict, fabric_catalog: dict = None) -> dict:
    """Build inverted index from garment and fabric keywords."""
    index = {}
    
    # Index garment keywords
    for name, garment in garment_catalog.items():
        for kw in garment.get("keywords", []):
            tokens = kw.lower().replace("-", " ").split()
            for token in tokens:
                if token not in STOP_WORDS and len(token) > 1:
                    if token not in index:
                        index[token] = []
                    index[token].append({
                        "source": name,
                        "source_type": "garment",
                        "keyword": kw,
                        "strength": 1.0,
                    })
    
    # Index fabric keywords
    if fabric_catalog:
        for name, fabric in fabric_catalog.items():
            for kw in fabric.get("keywords", []):
                tokens = kw.lower().replace("-", " ").split()
                for token in tokens:
                    if token not in STOP_WORDS and len(token) > 1:
                        if token not in index:
                            index[token] = []
                        index[token].append({
                            "source": name,
                            "source_type": "fabric",
                            "keyword": kw,
                            "strength": 1.0,
                        })
    
    return index


def search_by_keywords(tokens: list, index: dict, source_type: str = "") -> list:
    """Search index by keyword tokens, return ranked matches."""
    scores = {}
    matched_keywords = {}
    
    for token in tokens:
        entries = index.get(token, [])
        for entry in entries:
            if source_type and entry["source_type"] != source_type:
                continue
            key = (entry["source"], entry["source_type"])
            scores[key] = scores.get(key, 0) + entry["strength"]
            if key not in matched_keywords:
                matched_keywords[key] = []
            if token not in matched_keywords[key]:
                matched_keywords[key].append(token)
    
    results = []
    for (source, stype), score in scores.items():
        results.append({
            "source": source,
            "source_type": stype,
            "score": round(score, 2),
            "matched_keywords": matched_keywords[(source, stype)],
        })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def get_keywords_for_garment(garment: dict) -> list:
    """Get all keywords for a garment entry."""
    return garment.get("keywords", [])


def get_keywords_by_category(category: str) -> list:
    """Get keyword list for a category (mood, era, designer, etc)."""
    return KEYWORD_CATEGORIES.get(category, [])
