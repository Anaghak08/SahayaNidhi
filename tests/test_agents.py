# tests/test_agents.py

from app.agents.intake import analyze_intake

ALLOWED_CATEGORIES = [
    "open_drain",
    "pothole",
    "streetlight",
    "water_leak",
    "fallen_tree",
    "other"
]

SLA_MAP = {
    "critical": "4h",
    "high": "12h",
    "medium": "24h",
    "low": "72h"
}

def test_all_categories_and_fallback():
    test_cases = [
        ("Open drain uncovered near bus stop", "open_drain"),
        ("Large pothole at market entrance", "pothole"),
        ("Streetlight not working on park road", "streetlight"),
        ("Pipe burst with water flowing on road", "water_leak"),
        ("Tree fallen and blocking the road", "fallen_tree"),
        ("Something is wrong here", "other")
    ]

    for text, expected_category in test_cases:
        res = analyze_intake(text)

        # 1. Verify all required keys exist
        required_keys = [
            "category", "confidence", "severity_score", 
            "severity_level", "sla", "explanation", 
            "context_factors", "category_provider", "warning"
        ]
        for key in required_keys:
            assert key in res, f"Missing key '{key}' in return payload"

        # 2. Check category rules
        assert res["category"] in ALLOWED_CATEGORIES
        assert res["category"] == expected_category

        # 3. Check numeric score constraints
        assert 0.0 <= res["confidence"] <= 1.0
        assert 0.0 <= res["severity_score"] <= 1.0

        # 4. Check strict SLA mapping
        assert res["sla"] == SLA_MAP[res["severity_level"]]


def test_high_hazard_escalation():
    # Hazard word 'children' and 'fall' should escalate severity to critical (4h)
    text = "Open drain uncovered near bus stop; children may fall"
    res = analyze_intake(text)

    assert res["severity_level"] == "critical"
    assert res["sla"] == "4h"
    assert "child" in res["context_factors"] or "children" in res["context_factors"] or "fall" in res["context_factors"]