import re
from rapidfuzz import fuzz, process
from typing import List, Dict, Any, Tuple

def normalize_text(text: str) -> str:
    """
    Cleans punctuation, normalizes casing, and standardizes phonetic spellings
    to prevent false negatives in Hindi-to-English transliterations.
    """
    if not text:
        return ""
    
    # 1. Lowercase and strip
    text = text.lower().strip()
    
    # 2. Strip punctuation
    text = re.sub(r'[^\w\s]', '', text)
    
    # 3. Phonetic simplifications for Indian addresses
    phonetic_map = {
        "purwa": "purva",
        "gaon": "gram",
        "nagar": "ngr",
        "colony": "clny",
        "enclave": "encl",
        "vihar": "vhr",
        "khand": "khnd"
    }
    
    for word, replacement in phonetic_map.items():
        text = text.replace(word, replacement)
        
    return text

def resolve_geoname(query: str, known_localities: List[str], threshold: float = 75.0) -> Dict[str, Any]:
    """
    Fuzzy matches a user query against known database localities using RapidFuzz.
    Returns the resolved name, confidence, and match type.
    """
    normalized_query = normalize_text(query)
    
    if not known_localities:
        return {"resolved_name": query, "match_confidence": 0.0, "match_type": "no_database_coverage"}

    # 1. Exact Match Check (O(N) but fast)
    for loc in known_localities:
        if normalized_query == normalize_text(loc):
            return {
                "resolved_name": loc,
                "match_confidence": 1.0,
                "match_type": "exact_match"
            }
            
    # 2. Fuzzy Transliteration Match via RapidFuzz
    # Create mapping of normalized -> original
    norm_to_orig = {}
    for loc in known_localities:
        norm = normalize_text(loc)
        if norm not in norm_to_orig:
            norm_to_orig[norm] = loc
            
    choices = list(norm_to_orig.keys())
    
    # Extract best match using WRatio (handles partial word matches and minor typos well)
    result = process.extractOne(normalized_query, choices, scorer=fuzz.WRatio)
    
    if result and result[1] >= threshold:
        best_norm_match = result[0]
        score = result[1] / 100.0  # Normalize to 0.0 -> 1.0
        
        return {
            "resolved_name": norm_to_orig[best_norm_match],
            "match_confidence": round(score, 3),
            "match_type": "fuzzy_transliterated"
        }
        
    return {
        "resolved_name": query,
        "match_confidence": 0.0,
        "match_type": "no_match_found"
    }
