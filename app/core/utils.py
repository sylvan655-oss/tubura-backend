import re

DISTRICT_CODES = {
    "Bugesera": "BUG", "Burera": "BUR", "Gakenke": "GAK", "Gasabo": "GAS", "Gatsibo": "GAT",
    "Gicumbi": "GIC", "Gisagara": "GIS", "Huye": "HUY", "Kamonyi": "KAM", "Karongi": "KAR",
    "Kayonza": "KAY", "Kicukiro": "KIC", "Kirehe": "KIR", "Muhanga": "MUH", "Musanze": "MUS",
    "Ngoma": "NGO", "Ngororero": "NGR", "Nyabihu": "NYA", "Nyagatare": "NYG", "Nyamagabe": "NYM",
    "Nyamasheke": "NYS", "Nyanza": "NYN", "Nyarugenge": "NYR", "Nyaruguru": "NYU", "Rubavu": "RUB",
    "Ruhango": "RUH", "Rulindo": "RUL", "Rusizi": "RUS", "Rutsiro": "RUT", "Rwamagana": "RWA",
}


def normalize_phone(phone: str) -> str:
    """Normalize any Rwandan phone input to E.164-ish '+250XXXXXXXXX' form."""
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("250"):
        digits = digits[3:]
    digits = digits[-9:]  # keep last 9 digits
    return f"+250{digits}"


def district_code(district: str) -> str:
    return DISTRICT_CODES.get(district or "", "OAF")
