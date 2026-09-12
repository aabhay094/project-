"""
CIVIQ NLP Engine
----------------
Lightweight keyword/rule-based classifier that reads a citizen's free-text
grievance description (Hindi, English, or Hinglish) and returns:
    - matched sector slug
    - urgency level ('emergency', 'high', or 'standard')
    - list of matched keyword tags

This is deliberately dependency-free (no external NLP libraries) so it
runs anywhere, including constrained environments like Termux.

IMPORTANT: sector slugs here must exactly match the Sector.slug values
seeded by civiq/migrations/0002_seed_data.py.
"""

import re

# sector_slug -> list of keyword/phrase triggers (English, Hindi, Hinglish)
SECTOR_KEYWORDS = {
    "roads-potholes": [
        "pothole", "potholes", "gaddha", "gadde", "road damage", "broken road",
        "sadak tuti", "sadak kharab", "footpath", "road crack", "speed breaker damaged",
    ],
    "garbage-collection": [
        "garbage", "kooda", "kachra", "trash", "waste", "dustbin", "garbage not collected",
        "kooda nahi utha", "waste pile", "littering",
    ],
    "street-lighting": [
        "street light", "streetlight", "no streetlight", "light not working",
        "batti kharab", "andhera", "pole light",
    ],
    "stray-animals": [
        "stray dog", "stray animal", "awara pashu", "awara kutta", "dog bite",
        "cattle on road", "stray cattle",
    ],
    "illegal-encroachment": [
        "encroachment", "illegal construction", "illegal occupation", "footpath encroached",
        "kabja", "atikraman",
    ],
    "water-supply": [
        "no water supply", "water supply", "pani nahi aa raha", "low water pressure",
        "contaminated water", "ganda pani", "dirty water", "pani ki quality",
    ],
    "sewage-drainage": [
        "water leakage", "pani ki pipe", "pipe leak", "sewage overflow", "sewage",
        "drainage", "naali", "gutter", "drain blocked", "water logging", "jalbharav",
    ],
    "power-outage": [
        "sparking", "power cut", "bijli", "no electricity", "transformer",
        "voltage fluctuation", "electric pole", "wire hanging", "short circuit",
        "current", "light chali gayi",
    ],
    "power-billing": [
        "electricity bill", "bijli bill", "meter fault", "wrong bill", "excess bill",
        "meter reading galat",
    ],
    "traffic-signal": [
        "traffic signal", "signal not working", "traffic light", "signal kharab",
    ],
    "illegal-parking": [
        "illegal parking", "traffic jam", "encroached road", "zebra crossing",
        "wrong parking", "jam lagta hai",
    ],
    "mosquito-disease-control": [
        "mosquito", "dengue", "malaria", "epidemic", "machar", "fogging",
        "vaccination", "outbreak",
    ],
    "hospital-sanitation": [
        "hospital", "ambulance", "unclean hospital", "food adulteration", "clinic",
        "hospital ganda", "no doctor",
    ],
}

# Keywords that force an 'emergency' urgency regardless of sector
EMERGENCY_KEYWORDS = [
    "sparking", "fire", "aag", "collapsed", "gas leak", "electrocution",
    "short circuit", "dengue outbreak", "epidemic", "life threat", "accident",
    "wall collapse", "building collapse", "flooding", "children in danger",
    "exposed wire", "live wire",
]

HIGH_PRIORITY_KEYWORDS = [
    "no water supply", "sewage overflow", "power cut", "contaminated water",
    "road damage", "stray dog bite", "dog bite",
]


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def analyze_complaint(description: str):
    """
    Analyze the free-text complaint description.

    Returns a dict:
        {
            "sector_slug": str | None,
            "priority": "emergency" | "high" | "standard",
            "tags": [str, ...],
            "confidence": float (0-1),
        }
    """
    if not description:
        return {"sector_slug": None, "priority": "standard", "tags": [], "confidence": 0.0}

    normalized = _normalize(description)

    matched_tags = []
    sector_scores = {}

    for sector_slug, keywords in SECTOR_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in normalized:
                score += 1
                matched_tags.append(kw)
        if score:
            sector_scores[sector_slug] = score

    best_sector = None
    confidence = 0.0
    if sector_scores:
        best_sector = max(sector_scores, key=sector_scores.get)
        total_hits = sum(sector_scores.values())
        confidence = round(sector_scores[best_sector] / total_hits, 2)

    priority = "standard"
    if any(kw in normalized for kw in EMERGENCY_KEYWORDS):
        priority = "emergency"
    elif any(kw in normalized for kw in HIGH_PRIORITY_KEYWORDS):
        priority = "high"

    return {
        "sector_slug": best_sector,
        "priority": priority,
        "tags": sorted(set(matched_tags)),
        "confidence": confidence,
    }


# sector_slug -> human-readable department name, used only as a fallback
# label for the NLP preview if a Sector has no linked Department in the DB.
_DEPARTMENT_FALLBACK = {
    "roads-potholes": "Nagar Nigam (Roads & Sanitation)",
    "garbage-collection": "Nagar Nigam (Roads & Sanitation)",
    "street-lighting": "Nagar Nigam (Roads & Sanitation)",
    "stray-animals": "Nagar Nigam (Roads & Sanitation)",
    "illegal-encroachment": "Nagar Nigam (Roads & Sanitation)",
    "water-supply": "Jal Sansthan (Water & Drainage)",
    "sewage-drainage": "Jal Sansthan (Water & Drainage)",
    "power-outage": "MVVNL (Power / Discom)",
    "power-billing": "MVVNL (Power / Discom)",
    "traffic-signal": "Traffic & Urban Mobility",
    "illegal-parking": "Traffic & Urban Mobility",
    "mosquito-disease-control": "Public Health Department",
    "hospital-sanitation": "Public Health Department",
}


def suggest_department(sector_slug):
    """
    Human-readable department label for the real-time NLP preview shown on
    the Lodge Grievance page, before the Sector/Department DB lookup runs.
    """
    return _DEPARTMENT_FALLBACK.get(sector_slug, "General Grievance Cell")
