from backend.app.core.logging import logger
"""Dialogue Manager for step-by-step conversational eligibility checking across 10 Indian languages."""

from typing import Any

from backend.app.conversation.extractor import extract_all_facts, normalize_text
from backend.app.conversation.groq_client import groq_engine
from backend.app.conversation.indian_accent_llm import indian_accent_llm
from backend.app.conversation.knowledge_base import civic_knowledge
from backend.app.conversation.session import ConversationSession, MessageRecord
from backend.app.schemes.engine import check_scheme_eligibility, engine
from backend.app.schemes.models import EvaluationStatus, SchemeEvaluationResult

QUESTIONS_HI = {
    "age": {
        "text": "नमस्ते! कृपया अपनी आयु (उम्र) बताएं।",
        "options": ["18-30 वर्ष", "31-45 वर्ष", "46-60 वर्ष", "60 वर्ष से अधिक"]
    },
    "occupation": {
        "text": "आप क्या कार्य करते हैं? कृपया अपना मुख्य व्यवसाय बताएं।",
        "options": ["किसान (खेती)", "असंगठित मजदूर / दिहाड़ी", "छोटा दुकानदार / स्वरोजगार", "प्राइवेट नौकरी", "सरकारी नौकरी", "गृहिणी"]
    },
    "owns_cultivable_land": {
        "text": "क्या आपके परिवार के नाम पर कृषि योग्य भूमि (खेती की जमीन) है?",
        "options": ["हाँ, खेती की जमीन है", "नहीं, जमीन नहीं है"]
    },
    "is_income_tax_payer": {
        "text": "क्या आप या आपके परिवार का कोई सदस्य आयकर (इनकम टैक्स) भरता है?",
        "options": ["नहीं, टैक्स नहीं भरते", "हाँ, इनकम टैक्स भरते हैं"]
    },
    "monthly_income": {
        "text": "आपकी महीने की अनुमानित कमाई (मासिक आय) कितनी है?",
        "options": ["₹10,000 से कम", "₹10,000 - ₹15,000", "₹15,000 से अधिक"]
    },
    "covered_by_epfo_esic": {
        "text": "क्या आपका पीएफ (PF / EPFO) कटता है या सरकारी ईएसआईसी (ESIC) कार्ड बना है?",
        "options": ["नहीं, कोई पीएफ नहीं", "हाँ, पीएफ / ईएसआईसी है"]
    },
    "has_crop_loss": {
        "text": "क्या हाल ही में सूखे, भारी बारिश या कीट प्रकोप से आपकी फसल का 33% से अधिक नुकसान हुआ है?",
        "options": ["हाँ, फसल नुकसान हुआ है", "नहीं, फसल ठीक है"]
    },
    "gender": {
        "text": "कृपया अपना लिंग बताएं।",
        "options": ["महिला (Female)", "पुरुष (Male)", "अन्य (Other)"]
    },
    "is_pregnant_or_lactating": {
        "text": "क्या आप वर्तमान में गर्भवती हैं या छोटे शिशु को स्तनपान कराने वाली माता हैं?",
        "options": ["हाँ, गर्भवती / स्तनपान", "नहीं"]
    },
    "annual_income": {
        "text": "आपके परिवार की कुल वार्षिक आय (साल भर की कमाई) लगभग कितनी है?",
        "options": ["₹1 लाख से कम", "₹1 लाख - ₹2.5 लाख", "₹2.5 लाख से अधिक"]
    }
}

QUESTIONS_EN = {
    "age": {
        "text": "Namaste ji! Welcome. Kindly tell me your age.",
        "options": ["18-30 years", "31-45 years", "46-60 years", "Above 60 years"]
    },
    "occupation": {
        "text": "What is your primary occupation or livelihood?",
        "options": ["Farmer / Cultivator", "Daily Wage Laborer", "Shopkeeper / Self-Employed", "Private Salaried", "Government Job", "Homemaker"]
    },
    "owns_cultivable_land": {
        "text": "Does your family own cultivable agricultural land?",
        "options": ["Yes, we own land", "No, landless"]
    },
    "is_income_tax_payer": {
        "text": "Do you or any member of your household pay income tax?",
        "options": ["No, do not pay tax", "Yes, pay income tax"]
    },
    "monthly_income": {
        "text": "What is your approximate monthly income?",
        "options": ["Below ₹10,000", "₹10,000 - ₹15,000", "Above ₹15,000"]
    },
    "covered_by_epfo_esic": {
        "text": "Are you covered under formal EPFO / PF or ESIC?",
        "options": ["No, not covered", "Yes, covered by PF/ESIC"]
    },
    "has_crop_loss": {
        "text": "Did you suffer crop damage exceeding 33% due to natural calamity or drought?",
        "options": ["Yes, suffered crop loss", "No crop damage"]
    },
    "gender": {
        "text": "Please share your gender.",
        "options": ["Female", "Male", "Other"]
    },
    "is_pregnant_or_lactating": {
        "text": "Are you currently pregnant or a lactating mother?",
        "options": ["Yes, pregnant / lactating", "No"]
    },
    "annual_income": {
        "text": "What is your approximate annual household income in rupees?",
        "options": ["Below ₹1 Lakh", "₹1 Lakh - ₹2.5 Lakh", "Above ₹2.5 Lakh"]
    }
}

QUESTIONS_KN = {
    "age": {
        "text": "ನಮಸ್ಕಾರ! ದಯವಿಟ್ಟು ನಿಮ್ಮ ವಯಸ್ಸನ್ನು ತಿಳಿಸಿ.",
        "options": ["18-30 ವರ್ಷ", "31-45 ವರ್ಷ", "46-60 ವರ್ಷ", "60 ವರ್ಷ ಮೇಲ್ಪಟ್ಟು"]
    },
    "occupation": {
        "text": "ನಿಮ್ಮ ಮುಖ್ಯ ಕಸುಬು ಅಥವಾ ಉದ್ಯೋಗ ಯಾವುದು?",
        "options": ["ರೈತ (ಕೃಷಿ)", "ದಿನಗೂಲಿ ಕಾರ್ಮಿಕ", "ಸ್ವಯಂ ಉದ್ಯೋಗ / ಅಂಗಡಿ", "ಖಾಸಗಿ ಕೆಲಸ", "ಸರ್ಕಾರಿ ನೌಕರಿ", "ಗೃಹಿಣಿ"]
    },
    "owns_cultivable_land": {
        "text": "ನಿಮ್ಮ ಕುಟುಂಬದ ಹೆಸರಿನಲ್ಲಿ ಕೃಷಿ ಭೂಮಿ ಇದೆಯೇ?",
        "options": ["ಹೌದು, ಕೃಷಿ ಭೂಮಿ ಇದೆ", "ಇಲ್ಲ, ಭೂಮಿ ಇಲ್ಲ"]
    },
    "is_income_tax_payer": {
        "text": "ನೀವು ಅಥವಾ ನಿಮ್ಮ ಕುಟುಂಬದವರು ಆದಾಯ ತೆರಿಗೆ (Income Tax) ಪಾವತಿಸುತ್ತೀರಾ?",
        "options": ["ಇಲ್ಲ, ತೆರಿಗೆ ಕಟ್ಟುವುದಿಲ್ಲ", "ಹೌದು, ತೆರಿಗೆ ಕಟ್ಟುತ್ತೇವೆ"]
    },
    "monthly_income": {
        "text": "ನಿಮ್ಮ ಅಂದಾಜು ಮಾಸಿಕ ಆದಾಯ (ತಿಂಗಳ ಗಳಿಕೆ) ಎಷ್ಟು?",
        "options": ["₹10,000 ಕ್ಕಿಂತ ಕಡಿಮೆ", "₹10,000 - ₹15,000", "₹15,000 ಕ್ಕಿಂತ ಹೆಚ್ಚು"]
    },
    "covered_by_epfo_esic": {
        "text": "ನಿಮಗೆ ಪಿಎಫ್ (PF / EPFO) ಅಥವಾ ಇಎಸ್ಐಸಿ (ESIC) ಸೌಲಭ್ಯವಿದೆಯೇ?",
        "options": ["ಇಲ್ಲ, ಯಾವುದೇ ಪಿಎಫ್ ಇಲ್ಲ", "ಹೌದು, ಪಿಎಫ್/ಇಎಸ್ಐಸಿ ಇದೆ"]
    },
    "has_crop_loss": {
        "text": "ಬರ, ಅತಿಯಾದ ಮಳೆಯಿಂದ ನಿಮ್ಮ ಬೆಳೆ 33% ಕ್ಕಿಂತ ಹೆಚ್ಚು ಹಾನಿಯಾಗಿದೆಯೇ?",
        "options": ["ಹೌದು, ಬೆಳೆ ಹಾನಿಯಾಗಿದೆ", "ಇಲ್ಲ, ಬೆಳೆ ಸರಿಯಾಗಿದೆ"]
    },
    "gender": {
        "text": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಲಿಂಗವನ್ನು ತಿಳಿಸಿ.",
        "options": ["ಮಹಿಳೆ (Female)", "ಪುರುಷ (Male)", "ಇತರ (Other)"]
    },
    "is_pregnant_or_lactating": {
        "text": "ನೀವು ಪ್ರಸ್ತುತ ಗರ್ಭಿಣಿಯೇ ಅಥವಾ ಹಾಲುಣಿಸುವ ತಾಯಿಯೇ?",
        "options": ["ಹೌದು, ಗರ್ಭಿಣಿ/ಹಾಲುಣಿಸುವ ತಾಯಿ", "ಇಲ್ಲ"]
    },
    "annual_income": {
        "text": "ನಿಮ್ಮ ಕುಟುಂಬದ ವಾರ್ಷಿಕ ಆದಾಯ ಅಂದಾಜು ಎಷ್ಟು?",
        "options": ["₹1 ಲಕ್ಷಕ್ಕಿಂತ ಕಡಿಮೆ", "₹1 ಲಕ್ಷ - ₹2.5 ಲಕ್ಷ", "₹2.5 ಲಕ್ಷಕ್ಕಿಂತ ಹೆಚ್ಚು"]
    }
}

QUESTIONS_GU = {
    "age": {
        "text": "નમસ્તે! કૃપા કરીને તમારી ઉંમર જણાવો.",
        "options": ["18-30 વર્ષ", "31-45 વર્ષ", "46-60 વર્ષ", "60 વર્ષથી વધુ"]
    },
    "occupation": {
        "text": "તમે શું કામ કરો છો? તમારો મુખ્ય વ્યવસાય જણાવો.",
        "options": ["ખેડૂત (ખેતી)", "મજૂર / દૈનિક વેતન", "નાનો વેપારી / સ્વરોજગાર", "ખાનગી નોકરી", "સરકારી નોકરી", "ગૃહિણી"]
    },
    "owns_cultivable_land": {
        "text": "શું તમારા પરિવાર પાસે ખેતીલાયક જમીન છે?",
        "options": ["હા, જમીન છે", "ના, જમીન નથી"]
    },
    "is_income_tax_payer": {
        "text": "શું તમે કે તમારા પરિવારનો કોઈ સભ્ય ઇન્કમટેક્સ ભરે છે?",
        "options": ["ના, ટેક્સ નથી ભરતા", "હા, ઇન્કમટેક્સ ભરીએ છીએ"]
    },
    "monthly_income": {
        "text": "તમારી અંદાજિત માસિક આવક કેટલી છે?",
        "options": ["₹10,000 થી ઓછી", "₹10,000 - ₹15,000", "₹15,000 થી વધુ"]
    },
    "covered_by_epfo_esic": {
        "text": "શું તમારું પીએફ (PF) કપાય છે કે ESIC કાર્ડ છે?",
        "options": ["ના, પીએફ નથી", "હા, પીએફ/ESIC છે"]
    },
    "has_crop_loss": {
        "text": "શું દુષ્કાળ કે વધુ વરસાદથી તમારા પાકને 33% થી વધુ નુકસાન થયું છે?",
        "options": ["હા, પાક નુકસાન થયું છે", "ના, પાક બરાબર છે"]
    },
    "gender": {
        "text": "કૃપા કરીને તમારી જાતિ જણાવો.",
        "options": ["મહિલા", "પુરુષ", "અન્ય"]
    },
    "is_pregnant_or_lactating": {
        "text": "શું તમે હાલમાં ગર્ભવતી છો કે ધાત્રી માતા છો?",
        "options": ["હા, ગર્ભવતી / ધાત્રી", "ના"]
    },
    "annual_income": {
        "text": "તમારા પરિવારની કુલ વાર્ષિક આવક કેટલી છે?",
        "options": ["₹1 લાખથી ઓછી", "₹1 લાખ - ₹2.5 લાખ", "₹2.5 લાખથી વધુ"]
    }
}

QUESTIONS_TA = {
    "age": {
        "text": "வணக்கம்! தயவுசெய்து உங்கள் வயதைக் குறிப்பிடுங்கள்.",
        "options": ["18-30 வயது", "31-45 வயது", "46-60 வயது", "60 வயதுக்கு மேல்"]
    },
    "occupation": {
        "text": "உங்கள் முக்கிய தொழில் என்ன?",
        "options": ["விவசாயி (உழவர்)", "தினக்கூலி தொழிலாளி", "சுயதொழில் / கடை", "தனியார் வேலை", "அரசு வேலை", "இல்லத்தரசி"]
    },
    "owns_cultivable_land": {
        "text": "உங்கள் குடும்பத்திற்கு விவசாய நிலம் உள்ளதா?",
        "options": ["ஆம், நிலம் உள்ளது", "இல்லை, நிலம் இல்லை"]
    },
    "is_income_tax_payer": {
        "text": "நீங்கள் வருமான வரி (Income Tax) செலுத்துகிறீர்களா?",
        "options": ["இல்லை, வரி செலுத்தவில்லை", "ஆம், வரி செலுத்துகிறோம்"]
    },
    "monthly_income": {
        "text": "உங்கள் தோராயமான மாத வருமானம் எவ்வளவு?",
        "options": ["₹10,000-க்கு கீழ்", "₹10,000 - ₹15,000", "₹15,000-க்கு மேல்"]
    },
    "covered_by_epfo_esic": {
        "text": "உங்களுக்கு பிஎஃப் (PF) அல்லது இஎஸ்ஐசி (ESIC) உள்ளதா?",
        "options": ["இல்லை", "ஆம், பிஎஃப் உள்ளது"]
    },
    "has_crop_loss": {
        "text": "இயற்கை சீற்றத்தால் உங்கள் பயிர் 33% மேல் சேதமடைந்துள்ளதா?",
        "options": ["ஆம், பயிர் சேதமடைந்தது", "இல்லை, பயிர் சேதம் இல்லை"]
    },
    "gender": {
        "text": "தயவுசெய்து உங்கள் பாலினத்தைத் தேர்ந்தெடுக்கவும்.",
        "options": ["பெண்", "ஆண்", "மற்றவை"]
    },
    "is_pregnant_or_lactating": {
        "text": "நீங்கள் தற்போது கர்ப்பிணியாகவோ அல்லது பாலூட்டும் தாயாகவோ உள்ளீர்களா?",
        "options": ["ஆம், கர்ப்பிணி / தாய்", "இல்லை"]
    },
    "annual_income": {
        "text": "உங்கள் குடும்பத்தின் மொத்த ஆண்டு வருமானம் எவ்வளவு?",
        "options": ["₹1 லட்சத்திற்கு கீழ்", "₹1 லட்சம் - ₹2.5 லட்சம்", "₹2.5 லட்சத்திற்கு மேல்"]
    }
}

QUESTIONS_TE = {
    "age": {
        "text": "నమస్కారం! దయచేసి మీ వయస్సు తెలియజేయండి.",
        "options": ["18-30 సంవత్సరాలు", "31-45 సంవత్సరాలు", "46-60 సంవత్సరాలు", "60 ఏళ్లకు పైగా"]
    },
    "occupation": {
        "text": "మీ ముఖ్య వృత్తి లేదా పని ఏమిటి?",
        "options": ["రైతు (వ్యవసాయం)", "రోజువారీ కూలీ", "స్వయం ఉపాధి / దుకాణం", "ప్రైవేట్ ఉద్యోగం", "ప్రభుత్వ ఉద్యోగం", "గృహిణి"]
    },
    "owns_cultivable_land": {
        "text": "మీ కుటుంబానికి సాగు భూమి ఉందా?",
        "options": ["అవును, భూమి ఉంది", "లేదు, భూమి లేదు"]
    },
    "is_income_tax_payer": {
        "text": "మీరు ఆదాయపు పన్ను (Income Tax) చెల్లిస్తున్నారా?",
        "options": ["లేదు, పన్ను చెల్లించడం లేదు", "అవును, పన్ను చెల్లిస్తున్నాము"]
    },
    "monthly_income": {
        "text": "మీ సుమారు నెలవారీ ఆదాయం ఎంత?",
        "options": ["₹10,000 కంటే తక్కువ", "₹10,000 - ₹15,000", "₹15,000 కంటే ఎక్కువ"]
    },
    "covered_by_epfo_esic": {
        "text": "మీకు పీఎఫ్ (PF/EPFO) లేదా ఈఎస్ఐసీ (ESIC) సౌకర్యం ఉందా?",
        "options": ["లేదు", "అవును, ఉంది"]
    },
    "has_crop_loss": {
        "text": "కరువు లేదా వర్షాల వల్ల మీ పంట 33% కంటే ఎక్కువ నష్టపోయిందా?",
        "options": ["అవును, పంట నష్టపోయింది", "లేదు, పంట బాగానే ఉంది"]
    },
    "gender": {
        "text": "దయచేసి మీ లింగాన్ని ఎంచుకోండి.",
        "options": ["మహిళ", "పురుషుడు", "ఇతర"]
    },
    "is_pregnant_or_lactating": {
        "text": "మీరు ప్రస్తుతం గర్భిణీ లేదా బాలింత తల్లా?",
        "options": ["అవును", "కాదు"]
    },
    "annual_income": {
        "text": "మీ కుటుంబ వార్షిక ఆదాయం సుమారు ఎంత?",
        "options": ["₹1 లక్ష కంటే తక్కువ", "₹1 లక్ష - ₹2.5 లక్షలు", "₹2.5 లక్షల కంటే ఎక్కువ"]
    }
}

QUESTIONS_UR = {
    "age": {
        "text": "السلام علیکم! برائے مہربانی اپنی عمر بتائیں۔",
        "options": ["18-30 سال", "31-45 سال", "46-60 سال", "60 سال سے زیادہ"]
    },
    "occupation": {
        "text": "آپ کا بنیادی پیشہ یا کام کیا ہے؟",
        "options": ["کسان (کھیتی باڑی)", "مزدور / دیہاڑی دار", "چھوٹا دکاندار / خود روزگار", "پرائیویٹ ملازمت", "سرکاری ملازمت", "گھریلو خاتون"]
    },
    "owns_cultivable_land": {
        "text": "کیا آپ کے خاندان کی ملکیت میں زرعی زمین ہے؟",
        "options": ["ہاں، زمین ہے", "نہیں، زمین نہیں ہے"]
    },
    "is_income_tax_payer": {
        "text": "کیا آپ یا آپ کا کوئی فرد انکم ٹیکس ادا کرتا ہے؟",
        "options": ["نہیں، ٹیکس ادا نہیں کرتے", "ہاں، انکم ٹیکس دیتے ہیں"]
    },
    "monthly_income": {
        "text": "آپ کی ماہانہ آمدنی تقریباً کتنی ہے؟",
        "options": ["₹10,000 سے کم", "₹10,000 - ₹15,000", "₹15,000 سے زیادہ"]
    },
    "covered_by_epfo_esic": {
        "text": "کیا آپ کو پی ایف (PF) یا ای ایس آئی سی کی سہولت ہے؟",
        "options": ["نہیں", "ہاں، موجود ہے"]
    },
    "has_crop_loss": {
        "text": "کیا آپ کی فصل کو 33 فیصد سے زیادہ نقصان پہنچا ہے؟",
        "options": ["ہاں، نقصان ہوا ہے", "نہیں، فصل ٹھیک ہے"]
    },
    "gender": {
        "text": "برائے مہربانی اپنی جنس بتائیں۔",
        "options": ["خاتون", "مرد", "دیگر"]
    },
    "is_pregnant_or_lactating": {
        "text": "کیا آپ حاملہ یا دودھ پلانے والی ماں ہیں؟",
        "options": ["ہاں", "نہیں"]
    },
    "annual_income": {
        "text": "آپ کے خاندان کی سالانہ آمدنی کتنی ہے؟",
        "options": ["₹1 لاکھ سے کم", "₹1 لاکھ - ₹2.5 لاکھ", "₹2.5 لاکھ سے زیادہ"]
    }
}

QUESTIONS_OR = {
    "age": {
        "text": "ନମସ୍କାର! ଦୟାକରି ଆପଣଙ୍କ ବୟସ କୁହନ୍ତୁ।",
        "options": ["18-30 ବର୍ଷ", "31-45 ବର୍ଷ", "46-60 ବର୍ଷ", "60 ବର୍ଷରୁ ଅଧିକ"]
    },
    "occupation": {
        "text": "ଆପଣଙ୍କ ମୁଖ୍ୟ ବୃତ୍ତି ବା କାର୍ଯ୍ୟ କଣ?",
        "options": ["ଚାଷୀ (କୃଷି)", "ଦିନ ମଜୁରିଆ", "ଛୋଟ ଦୋକାନୀ / ସ୍ୱନିଯୁକ୍ତି", "ପ୍ରାଇଭେଟ୍ ଚାକିରି", "ସରକାରୀ ଚାକିରି", "ଗୃହିଣୀ"]
    },
    "owns_cultivable_land": {
        "text": "ଆପଣଙ୍କ ପରିବାର ନାମରେ ଚାଷ ଜମି ଅଛି କି?",
        "options": ["ହଁ, ଚାଷ ଜମି ଅଛି", "ନାହିଁ, ଜମି ନାହିଁ"]
    },
    "is_income_tax_payer": {
        "text": "ଆପଣ ଆୟକର (Income Tax) ଦିଅନ୍ତି କି?",
        "options": ["ନାହିଁ, ଟ୍ୟାକ୍ସ ଦେଉନାହୁଁ", "ହଁ, ଟ୍ୟାକ୍ସ ଦେଉଛୁ"]
    },
    "monthly_income": {
        "text": "ଆପଣଙ୍କ ମାସିକ ଆୟ କେତେ?",
        "options": ["₹10,000 ରୁ କମ୍", "₹10,000 - ₹15,000", "₹15,000 ରୁ ଅଧିକ"]
    },
    "covered_by_epfo_esic": {
        "text": "ଆପଣଙ୍କର ପିଏଫ୍ (PF) ବା ଇଏସଆଇସି (ESIC) ଅଛି କି?",
        "options": ["ନାହିଁ", "ହଁ, ଅଛି"]
    },
    "has_crop_loss": {
        "text": "ପ୍ରାକୃତିକ ବିପର୍ଯ୍ୟୟରେ 33% ରୁ ଅଧିକ ଫସଲ ନଷ୍ଟ ହୋଇଛି କି?",
        "options": ["ହଁ, ଫସଲ ନଷ୍ଟ ହୋଇଛି", "ନାହିଁ, ଫସଲ ଠିକ୍ ଅଛି"]
    },
    "gender": {
        "text": "ଦୟାକରି ଆପଣଙ୍କ ଲିଙ୍ଗ ଜଣାନ୍ତୁ।",
        "options": ["ମହିଳା", "ପୁରୁଷ", "ଅନ୍ୟ"]
    },
    "is_pregnant_or_lactating": {
        "text": "ଆପଣ ଗର୍ଭବତୀ କିମ୍ବା ସ୍ତନ୍ୟପାନ କରାଉଥିବା ମାଆ କି?",
        "options": ["ହଁ", "ନାହିଁ"]
    },
    "annual_income": {
        "text": "ଆପଣଙ୍କ ପରିବାରର ବାର୍ଷିକ ଆୟ କେତେ?",
        "options": ["₹1 ଲକ୍ଷରୁ କମ୍", "₹1 ଲକ୍ଷ - ₹2.5 ଲକ୍ଷ", "₹2.5 ଲକ୍ଷରୁ ଅଧିକ"]
    }
}

QUESTIONS_MR = {
    "age": {
        "text": "नमस्कार! कृपया तुमचे वय सांगा.",
        "options": ["18-30 वर्षे", "31-45 वर्षे", "46-60 वर्षे", "60 वर्षांपेक्षा जास्त"]
    },
    "occupation": {
        "text": "तुमचा मुख्य व्यवसाय किंवा काम काय आहे?",
        "options": ["शेतकरी (शेती)", "असंघटित कामगार / मजुरी", "छोटे व्यावसायिक / दुकानदार", "खाजगी नोकरी", "सरकारी नोकरी", "गृहिणी"]
    },
    "owns_cultivable_land": {
        "text": "तुमच्या कुटुंबाच्या नावावर शेतजमीन आहे का?",
        "options": ["होय, शेतजमीन आहे", "नाही, शेतजमीन नाही"]
    },
    "is_income_tax_payer": {
        "text": "तुम्ही किंवा कुटुंबातील कोणी इन्कम टॅक्स भरतात का?",
        "options": ["नाही, टॅक्स भरत नाही", "होय, इन्कम टॅक्स भरतो"]
    },
    "monthly_income": {
        "text": "तुमचे अंदाजे मासिक उत्पन्न (महिन्याची कमाई) किती आहे?",
        "options": ["₹10,000 पेक्षा कमी", "₹10,000 - ₹15,000", "₹15,000 पेक्षा जास्त"]
    },
    "covered_by_epfo_esic": {
        "text": "तुमचा पीएफ (PF) किंवा ESIC कार्ड आहे का?",
        "options": ["नाही, पीएफ नाही", "होय, पीएफ/ESIC आहे"]
    },
    "has_crop_loss": {
        "text": "दुष्काळ किंवा अतिवृष्टीमुळे पिकाचे 33% पेक्षा जास्त नुकसान झाले आहे का?",
        "options": ["होय, नुकसान झाले आहे", "नाही, पीक ठीक आहे"]
    },
    "gender": {
        "text": "कृपया तुमचे लिंग सांगा.",
        "options": ["महिला", "पुरुष", "इतर"]
    },
    "is_pregnant_or_lactating": {
        "text": "तुम्ही सध्या गर्भवती किंवा स्तनदा माता आहात का?",
        "options": ["होय, गर्भवती/स्तनदा माता", "नाही"]
    },
    "annual_income": {
        "text": "तुमच्या कुटुंबाचे वार्षिक उत्पन्न अंदाजे किती आहे?",
        "options": ["₹1 लाखापेक्षा कमी", "₹1 लाख - ₹2.5 लाख", "₹2.5 लाखापेक्षा जास्त"]
    }
}

QUESTIONS_ML = {
    "age": {
        "text": "നമസ്കാരം! ദയവായി നിങ്ങളുടെ പ്രായം പറയുക.",
        "options": ["18-30 വയസ്സ്", "31-45 വയസ്സ്", "46-60 വയസ്സ്", "60 വയസ്സിന് മുകളിൽ"]
    },
    "occupation": {
        "text": "നിങ്ങളുടെ പ്രധാന തൊഴിൽ എന്താണ്?",
        "options": ["കർഷകൻ (കൃഷി)", "കൂലിപ്പണിക്കാരൻ", "ചെറുകിട വ്യാപാരി / സ്വയംതൊഴിൽ", "സ്വകാര്യ ജോലി", "സർക്കാർ ജോലി", "വീട്ടമ്മ"]
    },
    "owns_cultivable_land": {
        "text": "നിങ്ങളുടെ കുടുംബത്തിന്റെ പേരിൽ കൃഷിഭൂമി ഉണ്ടോ?",
        "options": ["ഉണ്ട്, കൃഷിഭൂമി ഉണ്ട്", "ഇല്ല, ഭൂമിയില്ല"]
    },
    "is_income_tax_payer": {
        "text": "നിങ്ങൾ ഇൻകം ടാക്സ് (Income Tax) അടയ്ക്കുന്നുണ്ടോ?",
        "options": ["ഇല്ല, നികുതി അടയ്ക്കുന്നില്ല", "അതെ, നികുതി അടയ്ക്കുന്നുണ്ട്"]
    },
    "monthly_income": {
        "text": "നിങ്ങളുടെ പ്രതിമാസ വരുമാനം എത്രയാണ്?",
        "options": ["₹10,000-ൽ താഴെ", "₹10,000 - ₹15,000", "₹15,000-ൽ കൂടുതൽ"]
    },
    "covered_by_epfo_esic": {
        "text": "നിങ്ങൾക്ക് പി.എഫ് (PF) അല്ലെങ്കിൽ ഇ.എസ്.ഐ (ESIC) ഉണ്ടോ?",
        "options": ["ഇല്ല", "ഉണ്ട്"]
    },
    "has_crop_loss": {
        "text": "കാലാവസ്ഥാ വ്യതിയാനത്താൽ 33% ൽ കൂടുതൽ വിളനാശം സംഭവിച്ചിട്ടുണ്ടോ?",
        "options": ["ഉണ്ട്, വിളനാശം സംഭവിച്ചു", "ഇല്ല, കുഴപ്പമില്ല"]
    },
    "gender": {
        "text": "ദയവായി നിങ്ങളുടെ ലിംഗഭേദം വ്യക്തമാക്കുക.",
        "options": ["സ്ത്രീ", "പുരുഷൻ", "മറ്റുള്ളവ"]
    },
    "is_pregnant_or_lactating": {
        "text": "നിങ്ങൾ ഗർഭിണിയോ മുലയൂട്ടുന്ന അമ്മയോ ആണോ?",
        "options": ["അതെ", "അല്ല"]
    },
    "annual_income": {
        "text": "കുടുംബത്തിന്റെ വാർഷിക വരുമാനം എത്രയാണ്?",
        "options": ["₹1 ലക്ഷത്തിൽ താഴെ", "₹1 ലക്ഷം - ₹2.5 ലക്ഷം", "₹2.5 ലക്ഷത്തിന് മുകളിൽ"]
    }
}

QUESTIONS_MASTER = {
    "hi": QUESTIONS_HI,
    "en": QUESTIONS_EN,
    "kn": QUESTIONS_KN,
    "gu": QUESTIONS_GU,
    "ta": QUESTIONS_TA,
    "te": QUESTIONS_TE,
    "ur": QUESTIONS_UR,
    "or": QUESTIONS_OR,
    "mr": QUESTIONS_MR,
    "ml": QUESTIONS_ML,
}


class DialogueManager:
    def get_question(self, key: str, language: str = "hi") -> dict[str, Any]:
        table = QUESTIONS_MASTER.get(language, QUESTIONS_HI)
        fallback_table = QUESTIONS_HI
        return table.get(key, fallback_table.get(key, {"text": "Details needed", "options": []}))

    def find_next_question_key(self, session: ConversationSession) -> str | None:
        facts = session.facts

        # 1. Age is basic priority
        if facts.age is None:
            return "age"

        # 2. Occupation is fundamental
        if facts.occupation is None:
            return "occupation"

        # 3. If farmer:
        if facts.occupation == "farmer":
            if facts.owns_cultivable_land is None:
                return "owns_cultivable_land"
            if facts.is_income_tax_payer is None:
                return "is_income_tax_payer"
            if facts.has_crop_loss is None:
                return "has_crop_loss"

        # 4. If unorganized worker:
        if facts.occupation in ["unorganized_worker", "self_employed"]:
            if facts.monthly_income is None:
                return "monthly_income"
            if facts.covered_by_epfo_esic is None:
                return "covered_by_epfo_esic"
            if facts.is_income_tax_payer is None:
                return "is_income_tax_payer"

        # 5. Gender check if not known
        if facts.gender is None and facts.age is not None and facts.age >= 18 and facts.age <= 50:
            return "gender"

        # 6. If female and age >= 19, check maternal status for PMMVY
        if facts.gender == "female" and facts.age is not None and facts.age >= 19 and facts.is_pregnant_or_lactating is None:
            return "is_pregnant_or_lactating"

        # 7. Check annual income for general welfare
        if facts.annual_income is None and facts.monthly_income is None:
            return "annual_income"

        return None

    def _resolve_target_scheme(
        self, text: str, matched_schemes: list[SchemeEvaluationResult]
    ) -> SchemeEvaluationResult | None:
        norm = normalize_text(text)
        if any(k in norm for k in ["kisan", "pm kisan", "pm-kisan", "pmkisan", "kisaan", "किसान", "ખેડૂત", "ખેતી", "khet"]):
            for s in matched_schemes:
                if "kisan" in s.scheme_id.lower() or "kisan" in s.scheme_name.lower():
                    return s
        if any(k in norm for k in ["ayushman", "pm-jay", "pmjay", "jan arogya", "aarogya", "स्वास्थ्य", "इलाज", "आरोग्य", "आयुष्मान", "कार्ड", "હોસ્પિટલ", "આયુષ્માન", "આરોગ્ય"]):
            for s in matched_schemes:
                if "ayushman" in s.scheme_id.lower() or "jay" in s.scheme_id.lower() or "ayushman" in s.scheme_name.lower():
                    return s
        if any(k in norm for k in ["disaster", "fasal nuksan", "crop loss", "mukhyamantri", "फसल नुकसान", "आपदा", "मुआवजा", "સહાયતા", "પાક નુકસાન", "રાહત"]):
            for s in matched_schemes:
                if "crop" in s.scheme_id.lower() or "disaster" in s.scheme_id.lower() or "kss" in s.scheme_id.lower():
                    return s
        if any(k in norm for k in ["shram", "pension", "maan-dhan", "pmsym", "मजदूर", "श्रम", "पेंशन", "પેન્શન"]):
            for s in matched_schemes:
                if "sym" in s.scheme_id.lower() or "shram" in s.scheme_name.lower():
                    return s
        if any(k in norm for k in ["matru", "vandana", "pregnant", "garbhwati", "मातृत्व", "सगर्भा", "ધાત્રી"]):
            for s in matched_schemes:
                if "pmmvy" in s.scheme_id.lower() or "matru" in s.scheme_name.lower():
                    return s

        return matched_schemes[0] if matched_schemes else None

    def handle_post_completion(
        self,
        session: ConversationSession,
        user_text: str,
        source: str = "text",
        audio_confidence: float | None = None,
    ) -> dict[str, Any]:
        norm = normalize_text(user_text)

        # Check for restart / reset request
        if any(w in norm for w in ["restart", "reset", "shuru se", "फिर से", "शुरू से", "ಮೊದಲಿನಿಂದ", "மீண்டும்", "ફરીથી"]):
            session.facts = session.facts.__class__()
            session.messages.clear()
            session.current_question_key = "occupation"
            session.is_completed = False
            greeting_text = indian_accent_llm.format_greeting(session.language)
            q_occ = self.get_question("occupation", session.language)
            msg = MessageRecord(
                role="assistant",
                text=greeting_text,
                language=session.language,
                source="system",
            )
            session.messages.append(msg)
            return {
                "reply": greeting_text,
                "current_question_key": "occupation",
                "options": q_occ["options"],
                "facts": session.facts.model_dump(),
                "evaluation": [],
                "is_completed": False,
                "open_form_scheme_id": None,
                "detected_language": session.language,
            }

        # Language detection
        detected_lang = groq_engine.detect_language(user_text)
        if detected_lang in ["en", "hi", "gu"]:
            session.language = detected_lang

        user_msg = MessageRecord(
            role="user",
            text=user_text,
            language=session.language,
            source=source,
            audio_confidence=audio_confidence,
        )
        session.messages.append(user_msg)

        eval_results = engine.evaluate_all(session.facts)
        matched = [r for r in eval_results if r.status in [EvaluationStatus.POTENTIAL_MATCH, EvaluationStatus.MANUAL_REVIEW]]

        open_form_scheme_id: str | None = None
        target_scheme = self._resolve_target_scheme(user_text, matched)

        form_triggers = [
            "form", "apply", "fill", "registration", "register", "submit", "application",
            "फॉर्म", "फार्म", "भरना", "भर दो", "आवेदन", "अप्लाई", "भरें", "रजिस्टर", "भरिए",
            "ફોર્મ", "અરજી", "ભરવું", "ભરો", "ભરી આપો", "નોંધણી"
        ]

        details_triggers = [
            "detail", "details", "information", "benefit", "documents", "document", "tell me", "what is", "how much", "eligibility",
            "विवरण", "जानकारी", "डिटेल", "बताओ", "बताएं", "लाभ", "क्या मिलेगा", "कागजात", "दस्तावेज", "डॉक्यूमेंट", "पात्रता", "नियम",
            "વિગત", "માહિતી", "લાભ", "શું મળશે", "દસ્તાવેજ", "કાગળ", "જણાવો", "પાત્રતા", "નિયમો"
        ]

        # Case A: Form filling
        if any(k in norm for k in form_triggers):
            selected = target_scheme or (matched[0] if matched else None)
            open_form_scheme_id = selected.scheme_id if selected else "PM-KISAN"
            scheme_title = selected.scheme_name.split("(")[0].strip() if selected else "योजना"

            facts_summary = []
            if session.facts.age:
                facts_summary.append(f"आयु {session.facts.age} वर्ष" if session.language == "hi" else f"ઉંમર {session.facts.age} વર્ષ" if session.language == "gu" else f"Age {session.facts.age}")
            if session.facts.occupation:
                occ_label = "किसान" if session.facts.occupation == "farmer" and session.language == "hi" else "ખેડૂત" if session.facts.occupation == "farmer" and session.language == "gu" else session.facts.occupation
                facts_summary.append(occ_label)
            if session.facts.land_acres:
                facts_summary.append(f"{session.facts.land_acres} एकड़ जमीन" if session.language == "hi" else f"{session.facts.land_acres} એકર જમીન" if session.language == "gu" else f"{session.facts.land_acres} acres land")
            facts_str = ", ".join(facts_summary)

            # Use Groq LLM as primary responder if available
            groq_reply = ""
            if session.language in ["en", "hi", "gu"] and groq_engine.is_available():
                groq_reply = groq_engine.generate_form_fill_reply(
                    user_text=user_text,
                    scheme_name=scheme_title,
                    facts=session.facts.model_dump(),
                    language=session.language,
                )

            if groq_reply:
                reply = groq_reply
            elif session.language == "gu":
                reply = f"હા ચોક્કસ! મેં તમારી નોંધાયેલી વિગતો ({facts_str}) સાથે {scheme_title} નું અરજી ફોર્મ ભરી આપ્યું છે. કૃપા કરીને સ્ક્રીન પર ફોર્મ ચકાસી મંજૂરી આપો."
            elif session.language == "en":
                reply = f"Certainly! I have prefilled the application form for {scheme_title} using your verified details ({facts_str}). Please review the form on your screen and confirm."
            else:
                reply = f"जी, मैंने आपकी दर्ज जानकारी ({facts_str}) के आधार पर {scheme_title} का आवेदन फॉर्म तैयार कर दिया है। कृपया स्क्रीन पर खुले फॉर्म की समीक्षा करें और पुष्टि करें।"

            if session.language == "gu":
                options = ["ફોર્મ સબમિટ કરો (Submit)", "વિગતો સુધારો (Edit)", "અન્ય યોજનાઓ જુઓ"]
            elif session.language == "en":
                options = ["Submit Form", "Edit Details", "View Other Schemes"]
            else:
                options = ["फॉर्म जमा करें (Submit)", "विवरण सुधारें (Edit)", "अन्य योजनाएं देखें"]

        # Case B: Further details
        elif any(k in norm for k in details_triggers):
            selected = target_scheme or (matched[0] if matched else None)
            groq_reply = ""
            if session.language in ["en", "hi", "gu"] and groq_engine.is_available() and selected:
                groq_reply = groq_engine.generate_scheme_details_reply(
                    user_text=user_text,
                    scheme=selected,
                    language=session.language,
                )

            if groq_reply:
                reply = groq_reply
                scheme_title = selected.scheme_name.split("(")[0].strip() if selected else "योजना"
                if session.language == "gu":
                    options = [f"{scheme_title} નું ફોર્મ ભરો", "અન્ય યોજનાઓની વિગત જુઓ", "ફરીથી શરૂ કરો"]
                elif session.language == "en":
                    options = [f"Fill Form for {scheme_title}", "View Other Schemes", "Start Over"]
                else:
                    options = [f"{scheme_title} का फॉर्म भरें", "अन्य योजना का विवरण देखें", "शुरू से फिर जांचें"]
            elif selected:
                scheme_title = selected.scheme_name.split("(")[0].strip()
                benefit = selected.benefit_summary
                docs = ", ".join(selected.required_documents[:3])

                if session.language == "gu":
                    reply = f"{scheme_title}: મુખ્ય લાભ - {benefit}. જરૂરી દસ્તાવેજો: {docs}. ફોર્મ ભરવા માટે 'ફોર્મ ભરો' કહો."
                    options = [f"{scheme_title} નું ફોર્મ ભરો", "અન્ય યોજનાઓની વિગત જુઓ", "ફરીથી શરૂ કરો"]
                elif session.language == "en":
                    reply = f"{scheme_title}: Key benefit - {benefit}. Required documents: {docs}. Say 'fill form' to start form assistance."
                    options = [f"Fill Form for {scheme_title}", "View Other Schemes", "Start Over"]
                else:
                    reply = f"{scheme_title}: मुख्य लाभ - {benefit}। आवश्यक दस्तावेज: {docs}। आप इस योजना का फॉर्म भरने के लिए 'फॉर्म भरें' कह सकते हैं।"
                    options = [f"{scheme_title} का फॉर्म भरें", "अन्य योजना का विवरण देखें", "शुरू से फिर जांचें"]
            else:
                names = [m.scheme_name.split("(")[0].strip() for m in matched]
                if session.language == "gu":
                    reply = f"તમે {', '.join(names[:2])} માટે પાત્ર છો. તમે કોઈપણ યોજનાની વિગત પૂછી શકો છો અથવા ફોર્મ ભરવા કહી શકો છો."
                    options = ["પીએમ કિસાન યોજનાનું ફોર્મ ભરો", "યોજનાઓની વિગતો જુઓ", "ફરીથી શરૂ કરો"]
                elif session.language == "en":
                    reply = f"You are eligible for {', '.join(names[:2])}. Ask for specific details or say 'fill form' to begin application."
                    options = ["Fill PM-KISAN Form", "View Scheme Details", "Start Over"]
                else:
                    reply = f"आप {', '.join(names[:2])} के लिए पात्र हैं। आप किसी भी योजना की जानकारी ले सकते हैं या फॉर्म भरवाने के लिए 'फॉर्म भरें' कह सकते हैं।"
                    options = ["प्रधानमंत्री किसान योजना का फॉर्म भरें", "योजनाओं का विवरण देखें", "शुरू से फिर जांचें"]

        # Case C: General question
        else:
            groq_reply = ""
            if groq_engine.is_available():
                groq_reply = groq_engine.answer_any_question(
                    user_text=user_text,
                    context={"matched_schemes": [m.scheme_name for m in matched], "facts": session.facts.model_dump()},
                    language=session.language,
                )
                if not groq_reply:
                    groq_reply = groq_engine.generate_general_query_reply(
                        user_text=user_text,
                        matched_schemes=matched,
                        facts=session.facts.model_dump(),
                        language=session.language,
                    )

            if groq_reply:
                reply = groq_reply
                if session.language == "gu":
                    options = ["પીએમ કિસાન યોજનાનું ફોર્મ ભરો", "યોજનાઓની વિગતો જુઓ", "ફરીથી શરૂ કરો"]
                elif session.language == "en":
                    options = ["Fill Form Assistance", "View Scheme Details", "Start Over"]
                else:
                    options = ["फॉर्म भरने में सहायता लें", "योजनाओं का विवरण देखें", "शुरू से फिर जांचें"]
            else:
                knowledge_ans = civic_knowledge.find_knowledge_answer(user_text, session.language)
                if knowledge_ans:
                    reply = knowledge_ans
                    if session.language == "gu":
                        options = ["પીએમ કિસાન યોજનાનું ફોર્મ ભરો", "યોજનાઓની વિગતો જુઓ", "ફરીથી શરૂ કરો"]
                    elif session.language == "en":
                        options = ["Fill Form Assistance", "View Scheme Details", "Start Over"]
                    else:
                        options = ["फॉर्म भरने में सहायता लें", "योजनाओं का विवरण देखें", "शुरू से फिर जांचें"]
                elif session.language == "gu":
                    reply = f"તમે {', '.join([m.scheme_name.split('(')[0].strip() for m in matched[:2]])} માટે પાત્ર છો. શું તમે આ યોજનાનું ફોર્મ ભરવા માંગો છો કે વધુ વિગતો જાણવા માંગો છો?"
                    options = ["પીએમ કિસાન યોજનાનું ફોર્મ ભરો", "યોજનાઓની વિગતો જુઓ", "ફરીથી શરૂ કરો"]
                elif session.language == "en":
                    reply = f"You are eligible for {', '.join([m.scheme_name.split('(')[0].strip() for m in matched[:2]])}. Would you like me to fill the form or provide more details?"
                    options = ["Fill PM-KISAN Form", "View Scheme Details", "Start Over"]
                else:
                    reply = f"आप {', '.join([m.scheme_name.split('(')[0].strip() for m in matched[:2]])} के लिए पात्र हैं। क्या आप इसका फॉर्म भरना चाहते हैं या और विवरण जानना चाहते हैं?"
                    options = ["प्रधानमंत्री किसान योजना का फॉर्म भरें", "योजनाओं का विवरण देखें", "शुरू से फिर जांचें"]

        asst_msg = MessageRecord(
            role="assistant",
            text=reply,
            language=session.language,
            source="system",
        )
        session.messages.append(asst_msg)

        return {
            "reply": reply,
            "current_question_key": None,
            "options": options,
            "facts": session.facts.model_dump(),
            "evaluation": [r.model_dump() for r in eval_results],
            "is_completed": True,
            "tool_eligibility": check_scheme_eligibility(**session.facts.model_dump()),
            "detected_language": session.language,
            "open_form_scheme_id": open_form_scheme_id,
        }

    def process_message(
        self,
        session: ConversationSession,
        user_text: str,
        source: str = "text",
        audio_confidence: float | None = None,
    ) -> dict[str, Any]:
        session.update_activity()
        norm = normalize_text(user_text)
        clean_text = user_text.strip()

        is_first_interaction = len(session.messages) == 0

        # 1. Handle empty input / silence
        if clean_text == "":
            if is_first_interaction:
                session.current_question_key = "occupation"
                greeting_text = indian_accent_llm.format_greeting(session.language)
                q_occ = self.get_question("occupation", session.language)
                msg = MessageRecord(
                    role="assistant",
                    text=greeting_text,
                    language=session.language,
                    source="system",
                )
                session.messages.append(msg)
                return {
                    "reply": greeting_text,
                    "current_question_key": "occupation",
                    "options": q_occ["options"],
                    "facts": session.facts.model_dump(),
                    "evaluation": [],
                    "is_completed": False,
                }
            else:
                curr_k = session.current_question_key or "occupation"
                q_curr = self.get_question(curr_k, session.language)
                silence_prompt = indian_accent_llm.style_silence_prompt(session.language, curr_k)
                return {
                    "reply": silence_prompt,
                    "current_question_key": curr_k,
                    "options": q_curr["options"],
                    "facts": session.facts.model_dump(),
                    "evaluation": [],
                    "is_completed": False,
                }

        # 2. Handle session-start trigger or initial greeting
        greetings_list = ["hi", "hello", "namaste", "pranam", "vanakkam", "namaskara", "start", "shuru"]
        if clean_text == "[SESSION_START]" or (is_first_interaction and norm in greetings_list):
            session.current_question_key = "occupation"
            greeting_text = indian_accent_llm.format_greeting(session.language)
            q_occ = self.get_question("occupation", session.language)
            msg = MessageRecord(
                role="assistant",
                text=greeting_text,
                language=session.language,
                source="system",
            )
            session.messages.append(msg)
            return {
                "reply": greeting_text,
                "current_question_key": "occupation",
                "options": q_occ["options"],
                "facts": session.facts.model_dump(),
                "evaluation": [],
                "is_completed": False,
            }

        # Handle post-completion conversation (scheme details, form filling, clarifications)
        if session.is_completed:
            return self.handle_post_completion(
                session=session,
                user_text=user_text,
                source=source,
                audio_confidence=audio_confidence,
            )

        # 3. Handle restart request
        if any(w in norm for w in ["restart", "reset", "shuru se", "फिर से", "शुरू से", "ಮೊದಲಿನಿಂದ", "மீண்டும்"]):
            session.facts = session.facts.__class__()
            session.messages.clear()
            session.current_question_key = "occupation"
            greeting_text = indian_accent_llm.format_greeting(session.language)
            q_occ = self.get_question("occupation", session.language)
            msg = MessageRecord(
                role="assistant",
                text=greeting_text,
                language=session.language,
                source="system",
            )
            session.messages.append(msg)
            return {
                "reply": greeting_text,
                "current_question_key": "occupation",
                "options": q_occ["options"],
                "facts": session.facts.model_dump(),
                "evaluation": [],
                "is_completed": False,
            }

        # Analyze language using Groq LLM / script analyzer (for en, hi, gu)
        detected_lang = groq_engine.detect_language(user_text)
        prev_lang = session.language
        if detected_lang in ["en", "hi", "gu"]:
            session.language = detected_lang

        is_first_user_statement = len([m for m in session.messages if m.role == "user"]) == 0

        # Record citizen message
        user_msg = MessageRecord(
            role="user",
            text=user_text,
            language=session.language,
            source=source,
            audio_confidence=audio_confidence,
        )
        session.messages.append(user_msg)

        # Extract structured facts: Groq LLM + Deterministic rules
        groq_slots = groq_engine.extract_slots_with_groq(user_text, session.facts.model_dump(), session.language)
        extracted = extract_all_facts(user_text)
        for k, v in groq_slots.items():
            if k not in extracted or extracted[k] is None:
                extracted[k] = v

        # Extract situation intent for natural conversational empathy
        situation_intent = extracted.pop("_situation_intent", None)
        empathy_prefix = ""
        if situation_intent:
            if session.language == "gu":
                empathy_prefix = situation_intent.get("empathy_gu", "") + " "
            elif session.language == "hi":
                empathy_prefix = situation_intent.get("empathy_hi", "") + " "
            else:
                empathy_prefix = situation_intent.get("empathy_en", "") + " "

        # If current question was expecting a direct binary or option answer:
        curr_key = session.current_question_key
        if curr_key and curr_key not in extracted:
            # Check for yes/no responses to binary questions across languages
            yes_tokens = [
                "yes", "haan", "ha", "sahi", "हाँ", "हा", "सही", "ji haan",
                "ಹೌದು", "ಸರಿ", "ಹಾ", "ஆம்", "சரி", "అవును", "హా", "હા", "ہاں", "ହଁ", "होय", "അതെ"
            ]
            no_tokens = [
                "no", "nahi", "na", "गलत", "नहीं", "ना",
                "ಇಲ್ಲ", "ತಪ್ಪು", "இல்லை", "లేదు", "కాదు", "ના", "نہیں", "ନାହିଁ", "नाही", "അല്ല", "ഇല്ല"
            ]
            is_yes = any(w in norm for w in yes_tokens)
            is_no = any(w in norm for w in no_tokens)

            if curr_key in ["owns_cultivable_land", "is_income_tax_payer", "covered_by_epfo_esic", "is_pregnant_or_lactating", "has_crop_loss"]:
                if is_yes:
                    extracted[curr_key] = True
                elif is_no:
                    extracted[curr_key] = False

        # Apply extracted facts to session
        for k, v in extracted.items():
            setattr(session.facts, k, v)
            session.facts.fact_sources[k] = source
            session.facts.fact_confirmed[k] = True

        # Find next question
        next_key = self.find_next_question_key(session)
        session.current_question_key = next_key

        eval_results: list[SchemeEvaluationResult] = []
        is_completed = False

        if next_key is None:
            # All essential questions answered -> Run full deterministic evaluation
            is_completed = True
            session.is_completed = True
            eval_results = engine.evaluate_all(session.facts)

            matched = [r for r in eval_results if r.status in [EvaluationStatus.POTENTIAL_MATCH, EvaluationStatus.MANUAL_REVIEW]]
            matched_names = [m.scheme_name.split("(")[0].strip() for m in matched]

            # Use Groq LLM to deliver the conversational summary if available
            groq_summary = ""
            if session.language in ["en", "hi", "gu"] and groq_engine.is_available():
                groq_summary = groq_engine.generate_summary_reply(
                    matched_schemes=matched,
                    facts=session.facts.model_dump(),
                    language=session.language,
                )

            if groq_summary:
                reply = groq_summary
            else:
                reply = indian_accent_llm.style_summary(matched_names, session.language)

            options_map = {
                "hi": ["योजनाओं का विवरण देखें", "फॉर्म भरने में सहायता लें", "शुरू से फिर जांचें"],
                "en": ["View Scheme Details", "Get Form Assistance", "Start Over"],
                "kn": ["ಯೋಜನೆ ವಿವರಗಳನ್ನು ನೋಡಿ", "ಫಾರ್ಮ್ ಸಹಾಯ ಪಡೆಯಿರಿ", "ಮತ್ತೆ ಪ್ರಾರಂಭಿಸಿ"],
                "gu": ["યોજનાઓની વિગતો જુઓ", "ફોર્મ ભરવામાં મદદ મેળવો", "ફરીથી શરૂ કરો"],
                "ta": ["திட்ட விவரங்களைப் பார்க்கவும்", "படிவ உதவி பெறவும்", "மீண்டும் தொடங்கு"],
                "te": ["పథకాల వివరాలను చూడండి", "ఫారమ్ సహాయం పొందండి", "మళ్లీ ప్రారంభించండి"],
                "ur": ["اسکیموں کی تفصیلات دیکھیں", "فارم بھرنے में مدد لیں", "دوبارہ شروع کریں"],
                "or": ["ଯୋଜନାର ବିବରଣୀ ଦେଖନ୍ତୁ", "ଫର୍ମ ପୂରଣରେ ସହାୟତା ନିଅନ୍ତୁ", "ପୁଣି ଆରମ୍ଭ କରନ୍ତୁ"],
                "mr": ["योजनांचे तपशील पहा", "फॉर्म भरण्यास मदत घ्या", "पुन्हा सुरू करा"],
                "ml": ["പദ്ധതികളുടെ വിവരങ്ങൾ കാണുക", "ഫോം പൂരിപ്പിക്കാൻ സഹായം", "വീണ്ടും തുടങ്ങുക"],
            }
            options = options_map.get(session.language, options_map["hi"])
        else:
            q = self.get_question(next_key, session.language)

            # Check if user statement is an inquiry / question / information request
            is_inquiry = civic_knowledge.is_question_or_inquiry(user_text)
            knowledge_answer = ""
            if is_inquiry:
                # 1. Try Groq open-ended answer if available
                if session.language in ["en", "hi", "gu"] and groq_engine.is_available():
                    knowledge_answer = groq_engine.answer_any_question(
                        user_text=user_text,
                        context={"known_facts": session.facts.model_dump(), "pending_question": next_key},
                        language=session.language,
                    )
                # 2. If Groq unavailable or empty, check Civic Knowledge Base
                if not knowledge_answer:
                    knowledge_answer = civic_knowledge.find_knowledge_answer(user_text, session.language)

            if knowledge_answer:
                # User asked a question and we have an authoritative answer
                if len(extracted) > 0:
                    if session.language == "hi":
                        reply = f"{knowledge_answer} आगे बढ़ने के लिए, {q['text']}"
                    elif session.language == "gu":
                        reply = f"{knowledge_answer} આગળ વધવા માટે, {q['text']}"
                    else:
                        reply = f"{knowledge_answer} To proceed, {q['text']}"
                else:
                    if session.language == "hi":
                        reply = f"{knowledge_answer} आपकी पात्रता की जांच के लिए, {q['text']}"
                    elif session.language == "gu":
                        reply = f"{knowledge_answer} તમારી પાત્રતા તપાસવા માટે, {q['text']}"
                    else:
                        reply = f"{knowledge_answer} To check your eligibility, {q['text']}"
                options = q["options"]
            else:
                # Standard intake turn
                if curr_key and next_key == curr_key and len(extracted) == 0:
                    base_q = indian_accent_llm.style_clarification(next_key, session.language, user_text)
                else:
                    base_q = indian_accent_llm.style_question(q["text"], session.language, next_key)

                if empathy_prefix:
                    reply = f"{empathy_prefix}{base_q}".strip()
                else:
                    reply = base_q
                options = q["options"]

                # Strict deduplication defense: if reply is identical to previous assistant message, vary opening
                last_asst = next((m for m in reversed(session.messages) if m.role == "assistant"), None)
                if last_asst and last_asst.text.strip() == reply.strip():
                    if session.language == "hi":
                        reply = f"जी, स्पष्ट करने के लिए: {reply}"
                    elif session.language == "kn":
                        reply = f"ದಯವಿಟ್ಟು ಸ್ಪಷ್ಟಪಡಿಸಿ: {reply}"
                    else:
                        reply = f"Namaste ji, just to confirm: {reply}"

                # Primary answer engine via Groq LLM when available (English, Hindi, Gujarati)
                if session.language in ["en", "hi", "gu"] and groq_engine.is_available() and not is_completed:
                    groq_intake = groq_engine.generate_intake_reply(
                        user_text=user_text,
                        current_facts=session.facts.model_dump(),
                        next_question_key=next_key,
                        next_question_text=q["text"],
                        options=options,
                        language=session.language,
                    )
                    if groq_intake:
                        reply = groq_intake
                    else:
                        reply = groq_engine.style_reply_with_groq(user_text, reply, session.language)

        # Call structured check_scheme_eligibility tool to verify against deterministic database rules
        tool_eligibility = check_scheme_eligibility(**session.facts.model_dump())

        # Record assistant reply
        asst_msg = MessageRecord(
            role="assistant",
            text=reply,
            language=session.language,
            source="system",
        )
        session.messages.append(asst_msg)

        return {
            "reply": reply,
            "current_question_key": next_key,
            "options": options,
            "facts": session.facts.model_dump(),
            "evaluation": [r.model_dump() for r in eval_results],
            "is_completed": is_completed,
            "tool_eligibility": tool_eligibility,
            "detected_language": session.language,
            "open_form_scheme_id": None,
        }


dialogue_manager = DialogueManager()
