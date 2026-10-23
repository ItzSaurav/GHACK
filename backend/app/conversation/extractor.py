"""Deterministic and regex-based fact extractor for Multilingual (Hindi, English, Kannada, Tamil) speech and text."""

import re
from typing import Any

# Indic numerals (Devanagari, Gujarati, Kannada, Tamil) to standard ASCII digits
INDIC_DIGITS = str.maketrans("०१२३४५६७८९૦૧૨૩૪૫૬૭૮૯೦೧೨೩೪೫೬೭೮೯௦௧௨௩௪௫௬௭௮௯", "0123456789012345678901234567890123456789")

# Gujarati number words mapping
GUJARATI_NUMBER_WORDS = {
    "એક": 1, "બે": 2, "ત્રણ": 3, "ચાર": 4, "પાંચ": 5,
    "છ": 6, "સાત": 7, "આઠ": 8, "નવ": 9, "દસ": 10,
    "અગિયાર": 11, "બાર": 12, "તેર": 13, "ચૌદ": 14, "પંદર": 15,
    "સોળ": 16, "સત્તર": 17, "અઢાર": 18, "ઓગણીસ": 19, "વીસ": 20,
    "એકવીસ": 21, "બાવીસ": 22, "તેવીસ": 23, "ચોવીસ": 24, "પચ્ચીસ": 25,
    "છવીસ": 26, "સત્તાવીસ": 27, "અઠ્ઠાવીસ": 28, "ઓગણત્રીસ": 29, "ત્રીસ": 30,
    "એકત્રીસ": 31, "બત્રીસ": 32, "તેત્રીસ": 33, "ચોત્રીસ": 34, "પાંત્રીસ": 35,
    "ચાલીસ": 40, "પિસ્તાલીસ": 45, "પચાસ": 50, "પંચાવન": 55, "સાઈઠ": 60,
    "પાંસઠ": 65, "સિત્તેર": 70, "પંચોતેર": 75, "એંસી": 80, "નેવું": 90,
    "સો": 100, "હજાર": 1000, "લાખ": 100000, "કરોડ": 10000000,
}

# Hindi number words mapping
HINDI_NUMBER_WORDS = {
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5,
    "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15,
    "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19, "बीस": 20,
    "इक्कीस": 21, "बाईस": 22, "तेईस": 23, "चौबीस": 24, "पचीस": 25, "पच्चीस": 25,
    "छब्बीस": 26, "सत्ताईस": 27, "अट्ठाइस": 28, "उनतीस": 29, "तीस": 30,
    "इकतीस": 31, "बत्तीस": 32, "पैंतीस": 35, "चालीस": 40, "पैंतालीस": 45,
    "पचास": 50, "पचपन": 55, "साठ": 60, "पैंसठ": 65, "सत्तर": 70,
    "हजार": 1000, "हज़ार": 1000, "लाख": 100000, "करोड़": 10000000,
}

KANNADA_NUMBER_WORDS = {
    "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ನಾಲ್ಕು": 4, "ಐದು": 5, "ಆರು": 6,
    "ಏಳು": 7, "ಎಂಟು": 8, "ಒಂಬತ್ತು": 9, "ಹತ್ತು": 10, "ಇಪ್ಪತ್ತು": 20,
    "ಇಪ್ಪತ್ತೈದು": 25, "ಮೂವತ್ತು": 30, "ಮೂವತ್ತೈದು": 35, "ನಲವತ್ತು": 40, "ನಲವತ್ತೈದು": 45,
    "ಐವತ್ತು": 50, "ಅರವತ್ತು": 60, "ಎಪ್ಪತ್ತು": 70, "ಎಂಬತ್ತು": 80, "ತೊಂಬತ್ತು": 90,
    "ನೂರು": 100, "ಸಾವಿರ": 1000, "ಲಕ್ಷ": 100000, "ಕೋಟಿ": 10000000,
}

TAMIL_NUMBER_WORDS = {
    "ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5, "ஆறு": 6,
    "ஏழு": 7, "எட்டு": 8, "ஒன்பது": 9, "பத்து": 10, "இருபது": 20,
    "இருபத்தைந்து": 25, "முப்பது": 30, "முப்பத்தைந்து": 35, "நாற்பது": 40, "நாற்பத்தைந்து": 45,
    "ஐம்பது": 50, "அறுபது": 60, "எழுபது": 70, "எண்பது": 80, "தொண்ணூறு": 90,
    "நூறு": 100, "ஆயிரம்": 1000, "லட்சம்": 100000, "கோடி": 10000000,
}


def normalize_text(text: str) -> str:
    """Normalize text: convert Indic digits to ASCII and lowercase."""
    if not text:
        return ""
    converted = text.translate(INDIC_DIGITS)
    return converted.lower().strip()


def extract_age(text: str) -> int | None:
    norm = normalize_text(text)
    # Direct digit patterns across Hindi, English, Gujarati, Kannada, Tamil
    patterns = [
        r"(?:age|umar|umr|varsh|saal|साल|उम्र|आयु|ઉંમર|ઉમર|વય|વર્ષ|ವಯಸ್ಸು|ವರ್ಷ|வயது|வருடம்)(?:\s+(?:is|hai|h|था|थी|છે|છુ|હતી|આગಿದೆ))?[\s\:\=]*(\d{1,2})",
        r"(\d{1,2})\s*(?:saal|sal|years|yr|yrs|varsh|साल|वर्ष|વર્ષ|વર્ષનો|વર્ષની|વર્ષના|ವರ್ಷ|ವರ್ಷಗಳು|வயது|வருடம்)",
        r"(?:i am|am|main|હું|મારી ઉંમર|ನನಗೆ|எனக்கு)\s+(\d{1,2})\s*(?:years|saal|વર્ષ|ವರ್ಷ|வயது)?",
        r"^(\d{1,2})$",
    ]
    for p in patterns:
        m = re.search(p, norm)
        if m:
            val = int(m.group(1))
            if 0 < val <= 120:
                return val

    # Word-based age for Gujarati
    for word, val in GUJARATI_NUMBER_WORDS.items():
        if word in norm and ("વર્ષ" in norm or "ઉંમર" in norm or "ઉમર" in norm or "વય" in norm) and (0 < val <= 120):
            return val

    # Word-based age for Hindi
    for word, val in HINDI_NUMBER_WORDS.items():
        if word in norm and ("साल" in norm or "वर्ष" in norm or "उम्र" in norm or "saal" in norm) and (0 < val <= 120):
            return val

    # Word-based age for Kannada
    for word, val in KANNADA_NUMBER_WORDS.items():
        if word in norm and ("ವರ್ಷ" in norm or "ವಯಸ್ಸು" in norm) and (0 < val <= 120):
            return val

    # Word-based age for Tamil
    for word, val in TAMIL_NUMBER_WORDS.items():
        if word in norm and ("வயது" in norm or "வருடம்" in norm) and (0 < val <= 120):
            return val

    return None


def extract_income(text: str) -> tuple[int | None, str | None]:
    """Extract income amount and period ('monthly' or 'annual')."""
    norm = normalize_text(text)

    # Check period
    is_monthly = any(
        w in norm
        for w in [
            "mahina", "month", "pratimaah", "mahine", "महीना", "प्रतिमाह", "मासिक",
            "મહિને", "માસિક", "દર મહિને",
            "ತಿಂಗಳು", "ಮಾಸಿಕ", "மாதம்", "மாதாந்திர"
        ]
    )
    is_annual = any(
        w in norm
        for w in [
            "saal", "annual", "year", "varsh", "yearly", "वार्षिक", "सालाना",
            "વાર્ષિક", "વર્ષે", "વર્ષનું",
            "ವರ್ಷ", "ವಾರ್ಷಿಕ", "ஆண்டு", "வருடாந்திர"
        ]
    )

    period = "monthly" if is_monthly else ("annual" if is_annual else "monthly")

    # Match "k" multiplier: e.g. "12k" -> 12000
    m_k = re.search(r"(\d+(?:\.\d+)?)\s*k\b", norm)
    if m_k:
        return int(float(m_k.group(1)) * 1000), period

    # Match "lakh" multiplier across Hindi, Gujarati, Kannada, Tamil, English
    m_lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|लाख|લાખ|ಲಕ್ಷ|லட்சம்)", norm)
    if m_lakh:
        return int(float(m_lakh.group(1)) * 100000), "annual"

    # Match "thousand" / "hazar" / "savira" / "aayiram"
    m_hazar = re.search(r"(\d+)\s*(?:hazar|hazaar|thousand|हजार|हज़ार|હજાર|ಸಾವಿರ|ஆயிரம்)", norm)
    if m_hazar:
        return int(m_hazar.group(1)) * 1000, period

    # Direct digits
    m_digits = re.search(r"(?:income|kamata|salary|vetan|aay|rupaye|rs\.?|inr|आय|रुपये|कमाई|આવક|કમાણી|રૂપિયા|પગાર|ಆದಾಯ|ರೂಪಾಯಿ|வருமானம்|ரூபாய்)?\s*(\d{4,8})", norm)
    if m_digits:
        val = int(m_digits.group(1))
        if val >= 100000 and not is_monthly:
            period = "annual"
        return val, period

    return None, None


def extract_occupation(text: str) -> str | None:
    norm = normalize_text(text)

    # Farmer keywords (including dialect cues like "khet sookh gaya", "chhota kisan", "khedut")
    farmer_keys = [
        "farmer", "kisan", "kheti", "khetiwadi", "cultivat", "smallholder", "कृषि", "किसान", "खेती", "काश्तकार",
        "khet sookh", "fasal sookh", "sukha pad", "chhota kisan",
        "ખેડૂત", "ખેતી", "ખેતીવાડી", "નાનો ખેડૂત", "khedut",
        "ರೈತ", "ಕೃಷಿ", "ಬೆಳೆಗಾರ", "விவசாயி", "உழவர்", "பயிரிடுபவர்"
    ]
    if any(k in norm for k in farmer_keys):
        return "farmer"

    # Artisan / Handloom / Craftsperson
    artisan_keys = [
        "artisan", "karigar", "dastkar", "bunakar", "weaver", "potter", "handloom", "craftsman",
        "કારીગર", "વણકર", "શિલ્પકાર",
        "कारीगर", "दस्तकार", "बुनकर", "शिल्पकार", "हथकरघा", "ಕೈಮಗ್ಗ", "ಕುಶಲಕರ್ಮಿ", "கைவினைஞர்"
    ]
    if any(k in norm for k in artisan_keys):
        return "artisan"

    # Unorganized worker keywords (daily wage, laborer)
    unorg_keys = [
        "unorganized", "majdoor", "mazdoor", "daily wage", "vendor", "street vendor",
        "rehri", "thela", "rickshaw", "auto driver", "maid", "kamwali", "construction",
        "dihadi", "bhatta", "coolie", "hamali", "labourer", "laborer",
        "મજૂર", "મજૂરી", "દૈનિક મજૂર", "દૈનિક વેતન", "ફેરીવાળો", "લારી", "મજુરી",
        "मजदूर", "मजदूरी", "दिहाड़ी", "रेहड़ी", "ठेला", "रिक्शा", "असंगठित",
        "ದಿನಗೂಲಿ", "ಕೂಲಿ", "ಕಾರ್ಮಿಕ", "ದಿನಗೂಲಿ ಕಾರ್ಮಿಕ", "தினக்கூலி", "கூலி தொழிலாளி"
    ]
    if any(k in norm for k in unorg_keys):
        return "unorganized_worker"

    # Salaried Government
    govt_keys = [
        "govt", "sarkari", "sarkari naukri", "government officer", "सरकारी", "સરકારી નોકરી", "સરકારી અધિકારી",
        "ಸರ್ಕಾರಿ ಕೆಲಸ", "ಸರ್ಕಾರಿ ನೌಕರಿ", "ಅಧಿಕಾರಿ", "அரசு வேலை", "அரசு ஊழியர்"
    ]
    if any(k in norm for k in govt_keys):
        return "salaried_govt"

    # Salaried Private
    priv_keys = ["private job", "company", "mnc", "salaried", "प्राइवेट नौकरी", "ખાનગી નોકરી", "પ્રાઇવેટ નોકરી", "ಖಾಸಗಿ ಕೆಲಸ", "தனியார் வேலை"]
    if any(k in norm for k in priv_keys):
        return "salaried_private"

    # Self employed / business
    self_keys = [
        "business", "dukaan", "shop", "shopkeeper", "vyapar", "व्यापार", "दुकान", "खुद का काम",
        "દુકાન", "નાનો વેપારી", "સ્વરોજગાર", "ધંધો", "વેપાર",
        "ಸ್ವಯಂ ಉದ್ಯೋಗ", "ಅಂಗಡಿ", "ವ್ಯಾಪಾರ", "சுயதொழில்", "கடை", "வியாபாரம்"
    ]
    if any(k in norm for k in self_keys):
        return "self_employed"

    # Homemaker
    home_keys = ["housewife", "homemaker", "gharelu", "grihini", "गृहिणी", "घरेलू", "ગૃહિણી", "ઘરકામ", "ಗೃಹಿಣಿ", "ಮನೆ ಕೆಲಸ", "இல்லத்தரசி"]
    if any(k in norm for k in home_keys):
        return "homemaker"

    # Student
    student_keys = ["student", "padhai", "vidyarthi", "college fees", "fees", "scholarship", "વિદ્યાર્થી", "વિદ્યાર્થિની", "અભ્યાસ", "छात्र", "छात्रा", "पढ़ाई", "फीस", "ವಿದ್ಯಾರ್ಥಿ", "மாணவர்", "மாணவி"]
    if any(k in norm for k in student_keys):
        return "student"

    return None


def extract_gender(text: str) -> str | None:
    norm = normalize_text(text)

    female_keys = [
        "female", "woman", "girl", "aurat", "mahila", "stree", "ladki", "महिला", "स्त्री", "औरत", "लड़की",
        "મહિલા", "સ્ત્રી", "છોકરી",
        "ಮಹಿಳೆ", "ಹೆಣ್ಣು", "ಹೆಣ್ಣುಮಗಳು", "பெண்", "பெண்மணி"
    ]
    if any(re.search(rf"\b{k}\b", norm) for k in female_keys) or "महिला" in norm or "મહિલા" in norm or "ಮಹಿಳೆ" in norm or "பெண்" in norm:
        return "female"

    male_keys = [
        "male", "man", "boy", "purush", "aadmi", "ladka", "पुरुष", "आदमी", "लड़का",
        "પુરુષ", "ભાઈ", "છોકરો",
        "ಪುರುಷ", "ಗಂಡು", "ಗಂಡಸು", "ஆண்", "ஆண்மகன்"
    ]
    if any(re.search(rf"\b{k}\b", norm) for k in male_keys) or "पुरुष" in norm or "પુરુષ" in norm or "ಪುರುಷ" in norm or "ஆண்" in norm:
        return "male"

    return None


def extract_boolean_facts(text: str) -> dict[str, bool]:
    """Extract flags like land ownership, tax status, pregnancy, crop damage, epfo/pf."""
    norm = normalize_text(text)
    facts: dict[str, bool] = {}

    # Cultivable land ownership
    land_neg = [
        "no land", "zameen nahi", "jameen nahi", "landless", "bhoomiheen", "भूमिहीन", "जमीन नहीं", "खेत नहीं", "नहीं है",
        "જમીન નથી", "ખેતર નથી",
        "ಭೂಮಿ ಇಲ್ಲ", "ಜಮೀನು ಇಲ್ಲ", "ಭೂಹೀನ", "நிலம் இல்லை", "நிலமற்ற"
    ]
    land_pos = [
        "khet hai", "zameen hai", "jameen hai", "own land", "have land", "cultivable land", "जमीन है", "खेत है", "भूमि है",
        "જમીન છે", "ખેતર છે", "ખેતીની જમીન", "jamin chhe", "khet chhe",
        "ಭೂಮಿ ಇದೆ", "ಜಮೀನು ಇದೆ", "ಕೃಷಿ ಭೂಮಿ ಇದೆ", "ಹೊಲ ಇದೆ", "நிலம் உள்ளது", "விவசாய நிலம் உண்டு"
    ]
    if any(k in norm for k in land_neg):
        facts["owns_cultivable_land"] = False
    elif any(k in norm for k in land_pos):
        facts["owns_cultivable_land"] = True

    # Income tax payer
    tax_neg = [
        "tax nahi", "don't pay tax", "not a taxpayer", "income tax nahi", "टैक्स नहीं", "आयकर नहीं",
        "ટેક્સ નથી", "ટેક્સ નથી ભરતા", "ઇન્કમટેક્સ નથી",
        "ತೆರಿಗೆ ಇಲ್ಲ", "ತೆರಿಗೆ ಕಟ್ಟುವುದಿಲ್ಲ", "வரி இல்லை", "வரி செலுத்தவில்லை"
    ]
    tax_pos = [
        "tax bharta", "pay tax", "income tax deta", "taxpayer", "टैक्स भरता", "आयकर दाता",
        "ટેક્સ ભરીએ છીએ", "ઇન્કમટેક્સ ભરીએ છીએ",
        "ತೆರಿಗೆ ಕಟ್ಟುತ್ತೇವೆ", "ತೆರಿಗೆ ಪಾವತಿ", "வரி செலுத்துகிறோம்", "வருமான வரி செலுத்துபவர்"
    ]
    if any(k in norm for k in tax_neg):
        facts["is_income_tax_payer"] = False
    elif any(k in norm for k in tax_pos):
        facts["is_income_tax_payer"] = True

    # EPFO / PF / ESIC
    pf_neg = [
        "no pf", "pf nahi", "not covered by epfo", "पीएफ नहीं",
        "પીએફ નથી", "esic નથી",
        "ಪಿಎಫ್ ಇಲ್ಲ", "ಪಿಎಫ್ ಇಲ್ಲ", "பிஎஃப் இல்லை"
    ]
    pf_pos = [
        "pf katta", "epfo", "esic", "provident fund", "पीएफ",
        "પીએફ છે", "પીએફ કપાય છે", "esic છે",
        "ಪಿಎಫ್ ಇದೆ", "ಇಎಸ್ಐಸಿ", "பிஎஃப் உள்ளது", "இஎஸ்ஐசி"
    ]
    if any(k in norm for k in pf_neg):
        facts["covered_by_epfo_esic"] = False
    elif any(k in norm for k in pf_pos):
        facts["covered_by_epfo_esic"] = True

    # Pregnancy or lactating
    preg_neg = [
        "not pregnant", "garbhwati nahi", "गर्भवती नहीं",
        "ગર્ભવતી નથી",
        "ಗರ್ಭಿಣಿ ಅಲ್ಲ", "கர்ப்பமாக இல்லை"
    ]
    preg_pos = [
        "pregnant", "garbhwati", "baccha hone wala", "doodh pilati", "lactating", "गर्भवती", "स्तनपान", "धात्री",
        "ગર્ભવતી", "ધાત્રી", "સગર્ભા", "બાળક થવાનું છે",
        "ಗರ್ಭಿಣಿ", "ಹಾಲುಣಿಸುವ ತಾಯಿ", "கர்ப்பிணி", "பாலூட்டும் தாய்"
    ]
    if any(k in norm for k in preg_neg):
        facts["is_pregnant_or_lactating"] = False
    elif any(k in norm for k in preg_pos):
        facts["is_pregnant_or_lactating"] = True

    # Crop damage / loss
    crop_neg = [
        "no crop loss", "fasal thik", "no damage", "nuksan nahi", "nahi hua", "कोई नुकसान नहीं", "नुकसान नहीं", "नहीं हुआ", "फसल ठीक",
        "પાક બરાબર છે", "કોઈ નુકસાન નથી",
        "ಬೆಳೆ ಚೆನ್ನಾಗಿದೆ", "ಹಾನಿ ಇಲ್ಲ", "ನಷ್ಟ ಇಲ್ಲ", "பயிர் சேதம் இல்லை", "பாதிப்பு இல்லை"
    ]
    crop_pos = [
        "fasal kharab", "crop loss", "crop damage", "sookha pad gaya", "sookh gaya", "khet sookh", "sookh", "baadh", "nuksan hua",
        "પાક નુકસાન", "પાક બગડી ગયો", "દુષ્કાળ", "વરસાદથી નુકસાન", "પાક નિષ્ફળ", "નુકસાન થયું",
        "फसल बर्बाद", "फसल नुकसान", "सूखा", "सूख गया", "बाढ़",
        "ಬೆಳೆ ಹಾನಿಯಾಗಿದೆ", "ಬೆಳೆ ನಷ್ಟ", "ಬರ", "பயிர் சேதம்", "பயிர் இழப்பு", "வறட்சி", "வெள்ளம்"
    ]
    if any(k in norm for k in crop_neg):
        facts["has_crop_loss"] = False
    elif any(k in norm for k in crop_pos):
        facts["has_crop_loss"] = True

    return facts


DISTRICT_MAP = {
    # Bihar
    "patna": ("Bihar", "Patna"),
    "gaya": ("Bihar", "Gaya"),
    "muzaffarpur": ("Bihar", "Muzaffarpur"),
    "bhagalpur": ("Bihar", "Bhagalpur"),
    # Uttar Pradesh
    "varanasi": ("Uttar Pradesh", "Varanasi"),
    "lucknow": ("Uttar Pradesh", "Lucknow"),
    "gorakhpur": ("Uttar Pradesh", "Gorakhpur"),
    "kanpur": ("Uttar Pradesh", "Kanpur"),
    "prayagraj": ("Uttar Pradesh", "Prayagraj"),
    # Karnataka
    "mandya": ("Karnataka", "Mandya"),
    "mysuru": ("Karnataka", "Mysuru"),
    "mysore": ("Karnataka", "Mysuru"),
    "bengaluru": ("Karnataka", "Bengaluru"),
    "bangalore": ("Karnataka", "Bengaluru"),
    "belagavi": ("Karnataka", "Belagavi"),
    # Tamil Nadu
    "chennai": ("Tamil Nadu", "Chennai"),
    "madurai": ("Tamil Nadu", "Madurai"),
    "coimbatore": ("Tamil Nadu", "Coimbatore"),
    # Maharashtra
    "pune": ("Maharashtra", "Pune"),
    "mumbai": ("Maharashtra", "Mumbai"),
    "nagpur": ("Maharashtra", "Nagpur"),
    # Rajasthan
    "jaipur": ("Rajasthan", "Jaipur"),
    "jodhpur": ("Rajasthan", "Jodhpur"),
    # Madhya Pradesh
    "bhopal": ("Madhya Pradesh", "Bhopal"),
    "indore": ("Madhya Pradesh", "Indore"),
}


def extract_location(text: str) -> tuple[str | None, str | None]:
    """Extract (state, district) if present in text."""
    norm = normalize_text(text)

    # Check districts first (specific)
    for dist_key, (st, dist) in DISTRICT_MAP.items():
        if dist_key in norm:
            return st, dist

    # Check state names
    state_map = {
        "karnataka": "Karnataka",
        "ಕರ್ನಾಟಕ": "Karnataka",
        "tamil nadu": "Tamil Nadu",
        "तमिलनाडु": "Tamil Nadu",
        "uttar pradesh": "Uttar Pradesh",
        "up": "Uttar Pradesh",
        "उत्तर प्रदेश": "Uttar Pradesh",
        "bihar": "Bihar",
        "बिहार": "Bihar",
        "rajasthan": "Rajasthan",
        "राजस्थान": "Rajasthan",
        "madhya pradesh": "Madhya Pradesh",
        "mp": "Madhya Pradesh",
        "मध्य प्रदेश": "Madhya Pradesh",
        "maharashtra": "Maharashtra",
        "महाराष्ट्र": "Maharashtra",
        "gujarat": "Gujarat",
        "गुजरात": "Gujarat",
        "andhra pradesh": "Andhra Pradesh",
        "telangana": "Telangana",
        "odisha": "Odisha",
        "west bengal": "West Bengal",
        "kerala": "Kerala",
        "punjab": "Punjab",
        "haryana": "Haryana",
    }
    for k, v in state_map.items():
        if k in norm:
            return v, None

    return None, None


def extract_state_of_residence(text: str) -> str | None:
    state, _ = extract_location(text)
    return state


def extract_land_acres(text: str) -> float | None:
    norm = normalize_text(text)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:acre|acres|ekar|ekad|एकड़|एकर|એકર|વીઘા|ಎಕರೆ|ஏக்கர்)", norm)
    if m:
        try:
            return float(m.group(1))
        except (ValueError, TypeError):
            pass
    return None


def extract_social_category(text: str) -> str | None:
    norm = normalize_text(text)
    if any(k in norm for k in ["general", "samanya", "सामान्य", "જનરલ", "સામાન્ય", "जनरल", "ಜನರಲ್"]):
        return "general"
    if re.search(r"\bobc\b", norm) or any(k in norm for k in ["backward class", "pichhda", "पिछड़ा", "ઓબીસી", "પછાત", "ಹಿಂದುಳಿದ", "பிற்படுத்தப்பட்ட"]):
        return "obc"
    if re.search(r"\bsc\b", norm) or any(k in norm for k in ["scheduled caste", "dalit", "anusuchit jati", "अनुसूचित जाति", "અનુસૂચિત જાતિ", "ದಲಿತ", "ಪರಿಶಿಷ್ಟ ಜಾತಿ", "பட்டியலின"]):
        return "sc"
    if re.search(r"\bst\b", norm) or any(k in norm for k in ["scheduled tribe", "adivasi", "anusuchit janjati", "अनुसूचित जनजाति", "આદિવાસી", "અનુસૂચિત જનજાતિ", "ಪರಿಶಿಷ್ಟ ಪಂಗಡ", "பழங்குடி"]):
        return "st"
    return None


def extract_citizen_situation_intent(text: str) -> dict[str, Any]:
    """Identifies emotional/situational context for empathetic acknowledgment."""
    norm = normalize_text(text)
    intent: dict[str, Any] = {}

    if any(k in norm for k in ["sookh gaya", "sukha", "fasal kharab", "fasal barbad", "khet sookh", "damage", "પાક નુકસાન", "દુષ્કાળ", "પાક બગડી"]):
        intent["type"] = "crop_loss"
        intent["empathy_en"] = "I am very sorry to hear about your crop loss. Please don't worry, there are government relief and crop disaster schemes to assist you."
        intent["empathy_hi"] = "यह जानकर बहुत दुख हुआ कि आपकी फसल सूख गई या नुकसान हुआ है। बिल्कुल चिंता न करें, हम किसान राहत और मुआवजा योजनाओं की जांच करेंगे।"
        intent["empathy_gu"] = "તમારા પાકનું નુકસાન થયું તે જાણીને દુઃખ થયું. ચિંતા કરશો નહીં, અમે તમારા માટે કિસાન રાહત અને પાક નુકસાન યોજનાઓની તપાસ કરીશું."
    elif any(k in norm for k in ["college fees", "fees ke liye", "padhai", "scholarship", "fees madad", "કોલેજ ફી", "સ્કોલરશિપ", "અભ્યાસ"]):
        intent["type"] = "education_fees"
        intent["empathy_en"] = "Education is very important, and there are scholarship and education aid schemes available to support students."
        intent["empathy_hi"] = "पढ़ाई और कॉलेज फीस के लिए सरकार की कई छात्रवृत्ति (scholarship / education) योजनाएं हैं। हम आपके लिए सही योजना जरूर खोजेंगे।"
        intent["empathy_gu"] = "અભ્યાસ અને કોલેજ ફી માટે સરકારની વિવિધ શિષ્યવૃત્તિ (scholarship / education) યોજનાઓ ઉપલબ્ધ છે. અમે તમારા માટે યોગ્ય યોજના શોધીશું."
    elif any(k in norm for k in ["ilaj", "hospital", "dawa", "bimar", "bimaari", "treatment", "ઇલાજ", "હોસ્પિટલ", "દવા", "બીમાર"]):
        intent["type"] = "healthcare"
        intent["empathy_en"] = "Healthcare is essential, and you should never struggle alone. We will verify medical support and Ayushman Bharat coverage."
        intent["empathy_hi"] = "स्वास्थ्य सबसे महत्वपूर्ण है। हम आपके लिए मुफ्त इलाज और स्वास्थ्य सुरक्षा योजनाओं की जांच करेंगे।"
        intent["empathy_gu"] = "આરોગ્ય સૌથી મહત્વપૂર્ણ છે. અમે તમારા માટે આયુષ્માન ભારત અને આરોગ્ય સહાય યોજનાઓની તપાસ કરીશું."
    elif any(k in norm for k in ["khet", "zameen", "acre", "farming", "ખેડૂત", "ખેતી", "જમીન", "એકર"]):
        intent["type"] = "farming_support"
        intent["empathy_en"] = "Farming is the backbone of our country. Let us find suitable farmer welfare schemes for you."
        intent["empathy_hi"] = "किसान हमारे देश की रीढ़ हैं। हम आपके लिए उपयुक्त किसान कल्याण योजनाएं खोजेंगे।"
        intent["empathy_gu"] = "ખેડૂતો આપણા દેશનો આધાર છે. અમે તમારા માટે યોગ્ય ખેડૂત કલ્યાણકારી યોજનાઓ શોધીશું."

    return intent


def extract_all_facts(text: str) -> dict[str, Any]:
    """Combines all deterministic extractors over a single citizen utterance."""
    facts: dict[str, Any] = {}

    age = extract_age(text)
    if age is not None:
        facts["age"] = age

    inc, period = extract_income(text)
    if inc is not None:
        if period == "monthly":
            facts["monthly_income"] = inc
            facts["annual_income"] = inc * 12
        else:
            facts["annual_income"] = inc
            facts["monthly_income"] = inc // 12

    occ = extract_occupation(text)
    if occ is not None:
        facts["occupation"] = occ

    gender = extract_gender(text)
    if gender is not None:
        facts["gender"] = gender

    state, district = extract_location(text)
    if state is not None:
        facts["state_of_residence"] = state
    if district is not None:
        facts["district"] = district

    acres = extract_land_acres(text)
    if acres is not None:
        facts["land_acres"] = acres
        facts["land_hectares"] = round(acres * 0.404686, 2)
        facts["owns_cultivable_land"] = True

    cat = extract_social_category(text)
    if cat is not None:
        facts["social_category"] = cat

    bool_facts = extract_boolean_facts(text)
    facts.update(bool_facts)

    # Attach situation intent if found
    situation = extract_citizen_situation_intent(text)
    if situation:
        facts["_situation_intent"] = situation

    return facts
