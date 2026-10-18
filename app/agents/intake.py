# app/agents/intake.py

import re

# Allowed categories standard across the system
ALLOWED_CATEGORIES = [
    "open_drain",
    "pothole",
    "streetlight",
    "water_leak",
    "fallen_tree",
    "other"
]

# Keywords dictionary supporting English and Kannada terms/transliterations
CATEGORY_KEYWORDS = {
    "open_drain": ["drain", "gutter", "drainage", "sewer", "manhole", "morie", "kaaluve", "uncovered drain"],
    "pothole": ["pothole", "pit", "crater", "hole in road", "gundi", "road hole", "asphalt"],
    "streetlight": ["streetlight", "street light", "lamp", "light", "dark", "lighting", "geega", "beedhi deepa"],
    "water_leak": ["water leak", "pipe burst", "flowing water", "leakage", "water pipe", "neeru", "water main"],
    "fallen_tree": ["tree", "branch", "fallen tree", "maragalu", "mara", "blocked by tree"]
}

# Words indicating high hazard or immediate safety risks
HIGH_HAZARD_TERMS = [
    "child", "children", "fall", "fall in", "danger", "hazard", "sparking", 
    "live wire", "burst", "blocking road", "blocked", "accident", "injury", "school"
]


def _classify_by_keywords(description: str) -> tuple[str, float]:
    """Scans description text and returns predicted category and confidence."""
    text = description.lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                scores[cat] += 1

    best_cat = max(scores, key=scores.get)
    max_score = scores[best_cat]
    
    if max_score > 0:
        confidence = min(0.6 + (max_score * 0.15), 0.95)
        return best_cat, round(confidence, 2)
    
    return "other", 0.30


def _assess_severity(description: str, category: str) -> tuple[float, str, str, list]:
    """Calculates severity score (0.0-1.0), level, SLA, and detected risk factors."""
    text = description.lower()
    detected_hazards = [word for word in HIGH_HAZARD_TERMS if word in text]
    
    # Base score by category
    base_scores = {
        "open_drain": 0.6,
        "fallen_tree": 0.6,
        "water_leak": 0.5,
        "pothole": 0.4,
        "streetlight": 0.3,
        "other": 0.2
    }
    
    score = base_scores.get(category, 0.2)
    
    # Hazard multiplier / boost
    if detected_hazards:
        score += min(len(detected_hazards) * 0.15, 0.35)
    
    score = min(max(round(score, 2), 0.0), 1.0)
    
    # SLA Rules
    if score >= 0.75:
        severity_level = "critical"
        sla = "4h"
    elif score >= 0.55:
        severity_level = "high"
        sla = "12h"
    elif score >= 0.35:
        severity_level = "medium"
        sla = "24h"
    else:
        severity_level = "low"
        sla = "72h"
        
    return score, severity_level, sla, detected_hazards


def analyze_intake(description: str, declared_category: str = "other", weather_context: dict = None) -> dict:
    """
    Public function used by Member 5 and the frontend.
    Transforms complaint text into category, severity, SLA, and explanation.
    """
    # 1. Determine category locally via keywords
    predicted_cat, confidence = _classify_by_keywords(description)
    
    # Fallback to declared_category if keyword scan is uncertain
    category = predicted_cat if predicted_cat != "other" else (
        declared_category if declared_category in ALLOWED_CATEGORIES else "other"
    )
    
    # 2. Compute local severity and SLA rules
    sev_score, sev_level, sla, hazards = _assess_severity(description, category)
    
    # 3. Build plain language explanation
    explanation = f"Classified as '{category}' with {sev_level} priority ({sla} SLA)."
    if hazards:
        explanation += f" High hazard indicators detected: {', '.join(hazards)}."

    return {
        "category": category,
        "confidence": confidence,
        "severity_score": sev_score,
        "severity_level": sev_level,
        "sla": sla,
        "explanation": explanation,
        "context_factors": hazards,
        "category_provider": "local_keywords",
        "warning": None
    }