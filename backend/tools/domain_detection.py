from __future__ import annotations

from pathlib import Path


DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "finance": {"transaction", "account", "balance", "credit", "loan", "revenue", "profit"},
    "ecommerce": {"order", "cart", "sku", "customer", "product", "checkout", "discount"},
    "healthcare": {"patient", "diagnosis", "blood", "clinical", "provider", "claim"},
    "education": {"student", "grade", "course", "lms", "teacher", "enrollment"},
    "manufacturing": {"machine", "defect", "sensor", "downtime", "yield", "plant"},
    "marketing": {"campaign", "click", "impression", "conversion", "lead", "channel"},
    "retail": {"store", "inventory", "sku", "basket", "pos", "margin"},
    "hr": {"employee", "salary", "attrition", "tenure", "hiring", "performance"},
    "supply_chain": {"supplier", "shipment", "procurement", "warehouse", "stock", "delivery"},
    "telecom": {"subscriber", "call", "signal", "network", "churn", "tower"},
    "energy": {"grid", "load", "solar", "wind", "meter", "outage"},
    "government": {"citizen", "municipal", "permit", "tax", "agency", "district"},
    "real_estate": {"property", "listing", "zoning", "rent", "mortgage", "valuation"},
    "agriculture": {"crop", "soil", "harvest", "yield", "farm", "irrigation"},
    "cybersecurity": {"ip", "malware", "threat", "vulnerability", "incident", "alert"},
    "insurance": {"policy", "claim", "premium", "loss", "underwriting", "risk"},
    "pharmaceuticals": {"trial", "drug", "biomarker", "dose", "adverse", "compound"},
    "logistics": {"shipment", "route", "fleet", "delivery", "warehouse", "carrier"},
    "hospitality": {"booking", "hotel", "room", "guest", "occupancy", "revpar"},
    "travel": {"traveler", "flight", "booking", "itinerary", "fare", "route"},
    "media": {"content", "viewer", "subscription", "watch", "stream", "episode"},
    "gaming": {"player", "match", "level", "session", "currency", "quest"},
    "legal": {"contract", "clause", "matter", "case", "legal", "entity"},
    "construction": {"project", "bim", "rfi", "site", "contractor", "schedule"},
    "automotive": {"vehicle", "battery", "engine", "rpm", "telematics", "vin"},
    "aerospace": {"flight", "engine", "altitude", "aircraft", "maintenance", "fleet"},
    "oil_gas": {"well", "drilling", "reservoir", "pipeline", "barrel", "flow"},
    "nonprofit": {"donor", "gift", "campaign", "grant", "volunteer", "donation"},
    "public_sector": {"citizen", "program", "agency", "service", "case", "region"},
    "startup": {"runway", "burn", "mrr", "arr", "funding", "cohort"},
    "saas": {"tenant", "mrr", "arr", "churn", "subscription", "seat"},
    "mining_extraction": {"ore", "mine", "excavation", "grade", "haul", "drill"},
}


def available_domains(root: Path | None = None) -> list[str]:
    domain_root = root or Path("skills/business_domains")
    if not domain_root.exists():
        return sorted(DOMAIN_KEYWORDS)
    return sorted(path.stem for path in domain_root.glob("*.md"))


def detect_domain(columns: list[str]) -> dict[str, object]:
    normalized = {column.lower().replace("-", "_").replace(" ", "_") for column in columns}
    scores: dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for column in normalized:
            score += sum(1 for keyword in keywords if keyword in column)
        if score:
            scores[domain] = score

    if not scores:
        return {"domain": "general", "confidence": 0.0, "scores": {}}

    domain, score = max(scores.items(), key=lambda item: item[1])
    confidence = min(1.0, score / max(3, len(normalized)))
    return {"domain": domain, "confidence": round(confidence, 3), "scores": scores}
