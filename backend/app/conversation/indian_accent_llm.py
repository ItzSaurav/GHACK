"""Indian Accent LLM and Conversational Persona Engine.

Provides authentic Indian conversational styling across:
- English (Indian English accent, courtesy, and idioms: 'Namaste ji', 'kindly note', 'CSC Jan Seva Kendra')
- Hindi (Warm, respectful Jan Sahayak tone)
- Kannada (Courteous, regional administrative assistant tone)
- Tamil (Polite, clear community guide tone)

Ensures zero hallucination while making speech interactions warm, human, and culturally resonant.
"""

import os
import re
from typing import Any

from backend.app.core.logging import logger


class IndianAccentLLM:
    """Conversational persona engine delivering warm Indian context and accent styling."""

    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
        self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    def format_greeting(self, language: str = "hi") -> str:
        """Returns warm, accessible Seva Vaani spoken greeting under 2-3 concise sentences."""
        if language == "en":
            return (
                "Namaste ji! I am Seva Vaani, your voice helper for government schemes. "
                "Tell me a bit about your work or what assistance you are looking for today, and we will find the right scheme together."
            )
        elif language == "hi":
            return (
                "नमस्ते जी! मैं सेवा वाणी हूँ, सरकारी योजनाओं के लिए आपकी आवाज़ सहायता। "
                "मुझे अपने काम या आज आप किस सहायता की तलाश में हैं, इसके बारे में बताएं और हम मिलकर सही योजना खोजेंगे।"
            )
        elif language == "kn":
            return (
                "ನಮಸ್ಕಾರ! ನಾನು ಸೇವಾ ವಾಣಿ, ಸರ್ಕಾರಿ ಯೋಜನೆಗಳಿಗಾಗಿ ನಿಮ್ಮ ಧ್ವನಿ ಸಹಾಯಕ. "
                "ನಿಮ್ಮ ಕೆಲಸ ಅಥವಾ ಇಂದು ನಿಮಗೆ ಬೇಕಾದ ಸಹಾಯದ ಬಗ್ಗೆ ತಿಳಿಸಿ, ನಾವು ಒಟ್ಟಾಗಿ ಸೂಕ್ತ ಯೋಜನೆಯನ್ನು ಹುಡುಕೋಣ."
            )
        elif language == "ta":
            return (
                "வணக்கம்! நான் சேவா வாணி, அரசு நலத்திட்டங்களுக்கான உங்கள் குரல் உதவியாளர். "
                "உங்கள் வேலை பற்றியோ அல்லது உங்களுக்கு என்ன உதவி தேவை என்பதைப் பற்றியோ கூறுங்கள், நாம் சரியான திட்டத்தைக் கண்டறிவோம்."
            )
        elif language == "te":
            return (
                "నమస్కారం! నేను సేవా వాణి, ప్రభుత్వ పథకాల కోసం మీ వాయిస్ సహాయకుడిని. "
                "మీ పని లేదా మీకు ఏ సహాయం కావాలో చెప్పండి, మనం కలిసి సరైన పథకాన్ని కనుగొందాం."
            )
        elif language == "gu":
            return (
                "નમસ્તે! હું સેવા વાણી છું, સરકારી યોજનાઓ માટે તમારી અવાજ સહાયક. "
                "મને તમારા કામ અથવા આજે તમને કઈ સહાયની જરૂર છે તે જણાવો, આપણે સાથે મળીને યોગ્ય યોજના શોધીશું."
            )
        elif language == "mr":
            return (
                "नमस्ते! मी सेवा वाणी, सरकारी योजनांसाठी तुमची व्हॉइस मदतनीस. "
                "मला तुमच्या कामाबद्दल किंवा तुम्हाला कोणत्या मदतीची आवश्यकता आहे ते सांगा, आपण मिळून योग्य योजना शोधूया."
            )
        else:
            return (
                "Namaste! I am Seva Vaani, your voice helper for government schemes. "
                "Tell me a bit about your work or what assistance you are looking for today, and we will find the right scheme together."
            )

    def style_question(self, question_text: str, language: str = "hi", question_key: str = "") -> str:
        """Apply respectful Indian conversational framing to questions, keeping responses under 2-3 sentences."""
        if language == "en":
            # Infuse polite Indian conversational English phrasing
            if "age" in question_key:
                return "Namaste ji! Kindly tell me your age."
            elif "occupation" in question_key:
                return "Could you share what work you do, such as farming, daily wage work, study, or small business?"
            elif "owns_cultivable_land" in question_key or "land_acres" in question_key:
                return "Understood. Does your family possess any cultivable agricultural land, and about how many acres?"
            elif "location" in question_key or "state" in question_key:
                return "Which state and district do you live in?"
            elif "social_category" in question_key:
                return "Which social category do you belong to, such as General, OBC, SC, or ST?"
            elif "is_income_tax_payer" in question_key:
                return "Kindly tell me, does anyone in your household pay income tax?"
            elif "monthly_income" in question_key:
                return "What would be your approximate monthly earnings or income?"
            elif "annual_income" in question_key:
                return "What is your approximate total annual family income in rupees?"
            elif "covered_by_epfo_esic" in question_key:
                return "Are you or your spouse covered under formal PF, EPFO, or ESIC?"
            elif "has_crop_loss" in question_key:
                return "Did you suffer more than 33% crop damage due to drought, unseasonal rains, or pest attack?"
            elif "gender" in question_key:
                return "Please share your gender so I can identify women and maternity-specific schemes."
            elif "is_pregnant_or_lactating" in question_key:
                return "Kindly share if you are currently pregnant or a lactating mother."
            return question_text
        elif language == "kn":
            return question_text
        elif language == "ta":
            return question_text
        else:
            # Hindi conversational courtesy
            if not question_text.startswith("नमस्ते") and not question_text.startswith("जी"):
                return f"जी, {question_text}"
            return question_text

    def format_groq_acknowledgment(self, language: str = "en") -> str:
        """Deprecated: retained for backwards compatibility."""
        return ""

    def style_summary(
        self,
        matched_schemes: list[str],
        language: str = "hi",
    ) -> str:
        """Style final eligibility summary with empathetic Indian civic assistance tone."""
        count = len(matched_schemes)
        scheme_list = ", ".join(f"'{s}'" for s in matched_schemes)

        if count > 0:
            if language == "gu":
                return (
                    f"અભિનંદન! તમારી વિગતોના આધારે, તમે {count} સરકારી યોજના(ઓ) માટે સંભાવ્ય રીતે પાત્ર છો: "
                    f"{scheme_list}. "
                    f"કૃપા કરીને નીચે દરેક યોજનાના નિયમો, લાભો અને જરૂરી દસ્તાવેજોની ચકાસણી કરો. "
                    f"તમે ફોર્મ ભરવામાં પણ સહાય મેળવી શકો છો."
                )
            elif language == "hi":
                return (
                    f"बधाई हो जी! आपके द्वारा दी गई जानकारी के अनुसार, आप {count} सरकारी योजना(ओं) के लिए संभावित रूप से पात्र हैं: "
                    f"{scheme_list}। "
                    f"कृपया नीचे प्रत्येक योजना के नियम, लाभ और आवश्यक दस्तावेजों की समीक्षा करें। "
                    f"आप फॉर्म भरने के लिए भी सहायता ले सकते हैं।"
                )
            elif language == "kn":
                return (
                    f"ಅಭಿನಂದನೆಗಳು! ನಿಮ್ಮ ವಿವರಗಳ ಆಧಾರದ ಮೇಲೆ, ನೀವು {count} ಸರ್ಕಾರಿ ಯೋಜನೆಗಳಿಗೆ ಸಂಭಾವ್ಯವಾಗಿ ಅರ್ಹರಾಗಿದ್ದೀರಿ: "
                    f"{scheme_list}. "
                    f"ದಯವಿಟ್ಟು ಕೆಳಗೆ ಪ್ರತಿಯೊಂದು ಯೋಜನೆಯ ವಿವರಗಳು, ಲಾಭಗಳು ಮತ್ತು ಅಗತ್ಯ ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ."
                )
            elif language == "ta":
                return (
                    f"வாழ்த்துகள்! நீங்கள் பகிர்ந்த விவரங்களின்படி, நீங்கள் {count} அரசு திட்டங்களுக்கு தகுதிபெற வாய்ப்புள்ளது: "
                    f"{scheme_list}. "
                    f"தயவுசெய்து கீழே உள்ள திட்டங்களின் விவரங்கள், பலன்கள் மற்றும் தேவையான ஆவணங்களை மதிப்பாய்வு செய்யவும்."
                )
            else:
                return (
                    f"Great news ji! Based on the details you kindly provided, you potentially qualify for {count} government scheme(s): "
                    f"{scheme_list}. "
                    f"Kindly review the verified criteria, benefits, and required documents below. "
                    f"You can also proceed with step-by-step form assistance."
                )
        else:
            if language == "gu":
                return (
                    "વર્તમાન માહિતી મુજબ અમારી યાદીમાં કોઈ સીધો મેળ મળ્યો નથી. "
                    "ચિંતા કરશો નહીં, આનો અર્થ એ નથી કે તમે તમામ સરકારી યોજનાઓ માટે અપાત્ર છો. "
                    "તમે તમારા નજીકના સામાન્ય સેવા કેન્દ્ર (CSC / જન સેવા કેન્દ્ર) પર વધારાની યોજનાઓ તપાસી શકો છો."
                )
            elif language == "hi":
                return (
                    "वर्तमान जानकारी के अनुसार हमारे कैटलॉग में कोई प्रत्यक्ष मेल नहीं मिला। "
                    "कृपया चिंता न करें, इसका अर्थ यह बिल्कुल नहीं है कि आप सभी सरकारी योजनाओं से बाहर हैं। "
                    "आप अपने नजदीकी सीएससी (जन सेवा केंद्र) जाकर अन्य राज्य व केंद्रीय योजनाओं की पुष्टि कर सकते हैं।"
                )
            elif language == "kn":
                return (
                    "ಪ್ರಸ್ತುತ ವಿವರಗಳ ಪ್ರಕಾರ ನಮ್ಮ ಪಟ್ಟಿಯಲ್ಲಿ ನೇರ ಹೊಂದಾಣಿಕೆ ಕಂಡುಬಂದಿಲ್ಲ. "
                    "ಆದರೆ ಚಿಂತಿಸಬೇಡಿ, ನೀವು ಎಲ್ಲಾ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳಿಂದ ಹೊರಗಿದ್ದೀರಿ ಎಂದು ಇದರರ್ಥವಲ್ಲ. "
                    "ನಿಮ್ಮ ಹತ್ತಿರದ ಗ್ರಾಮ ಒನ್ ಅಥವಾ ಸಿಎಸ್‌ಸಿ ಕೇಂದ್ರದಲ್ಲಿ ಇತರ ಯೋಜನೆಗಳನ್ನು ವಿಚಾರಿಸಬಹುದು."
                )
            elif language == "ta":
                return (
                    "தற்போதைய தகவல்களின்படி எங்கள் பட்டியலில் நேரடி பொருத்தம் எதுவும் கிடைக்கவில்லை. "
                    "கவலைப்பட வேண்டாம், நீங்கள் அனைத்து அரசு திட்டங்களுக்கும் தகுதியற்றவர் என்று அர்த்தமல்ல. "
                    "உங்கள் அருகிலுள்ள இ-சேவை மையம் அல்லது சிஎஸ்சி மையத்தில் கூடுதல் திட்டங்களை விசாரிக்கலாம்."
                )
            else:
                return (
                    "Based on the provided facts, no direct match was found in our verified catalogue ji. "
                    "Please do not worry, this does not mean you are ineligible for all government welfare programs. "
                    "You can visit your nearest Common Service Center (CSC / Jan Seva Kendra) to check additional schemes."
                )

    def style_silence_prompt(self, language: str = "hi", question_key: str = "") -> str:
        """Returns warm, polite prompt when silence or low-energy audio is detected."""
        if language == "en":
            return "I could not hear you clearly ji. Could you please repeat your answer or speak a little louder?"
        elif language == "hi":
            return "क्षमा करें जी, मुझे आपकी आवाज़ स्पष्ट सुनाई नहीं दी। क्या आप कृपया थोड़ा साफ़ बोलकर दोहरा सकते हैं?"
        elif language == "kn":
            return "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಧ್ವನಿ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಸ್ಪಷ್ಟವಾಗಿ ತಿಳಿಸುವಿರಾ?"
        elif language == "ta":
            return "மன்னிக்கவும், உங்கள் குரல் தெளிவாகக் கேட்கவில்லை. தயவுசெய்து மீண்டும் சத்தமாக கூறவும்."
        elif language == "te":
            return "క్షమించండి, మీ వాయిస్ స్పష్టంగా వినపడలేదు. దయచేసి మళ్లీ కొంచెం గట్టిగా చెప్పగలరా?"
        elif language == "gu":
            return "માફ કરશો, તમારો અવાજ સ્પષ્ટ સંભળાયો નથી. કૃપા કરીને થોડું મોટેથી ફરીથી કહો."
        elif language == "mr":
            return "माफ करा, तुमचा आवाज स्पष्ट आला नाही. कृपया थोडे स्पष्ट आणि मोठ्याने पुन्हा सांगा."
        else:
            return "I could not hear you clearly ji. Could you please repeat your answer or speak a little louder?"

    def style_clarification(
        self, question_key: str, language: str = "hi", user_text: str = ""
    ) -> str:
        """Provide empathetic, natural Indian conversational clarification instead of repeating the same prompt."""
        if language == "en":
            if "occupation" in question_key:
                return (
                    "Got it ji. To verify your scheme eligibility, could you kindly specify if your work is "
                    "farming, daily wage labour, small business, or private employment?"
                )
            elif "age" in question_key:
                return "Understood. Kindly share your approximate age in years (for example, 35 or 45 years)."
            elif "owns_cultivable_land" in question_key or "land_acres" in question_key:
                return "Just to confirm ji, does your family own any farming land? You can reply with a simple 'Yes' or 'No'."
            elif "is_income_tax_payer" in question_key:
                return "To assist you with the right criteria, does anyone in your family pay income tax?"
            elif "monthly_income" in question_key:
                return "Could you kindly share roughly how much you earn each month, such as under ₹10,000 or more?"
            elif "annual_income" in question_key:
                return "Approximately how much is your entire household's yearly income in rupees?"
            elif "covered_by_epfo_esic" in question_key:
                return "Are you or your spouse covered under government EPFO or ESIC? A simple 'Yes' or 'No' will help."
            elif "has_crop_loss" in question_key:
                return "Did your farm experience over 33% crop damage from drought or rain?"
            return f"Understood ji. To help find the right scheme, please share your {question_key.replace('_', ' ')}."
        elif language == "hi":
            if "occupation" in question_key:
                return (
                    "जी, समझ गया। सही योजना खोजने के लिए, क्या आप मुख्य रूप से खेती, "
                    "दिहाड़ी मजदूरी, छोटा व्यापार या प्राइवेट नौकरी करते हैं?"
                )
            elif "age" in question_key:
                return "कृपया अपनी अनुमानित उम्र बताएं (जैसे 30 साल या 45 साल) ताकि सही आयु वर्ग की योजनाएं मिल सकें।"
            elif "owns_cultivable_land" in question_key or "land_acres" in question_key:
                return "जी, पुष्टि के लिए कृपया 'हाँ' या 'ना' में बताएं कि क्या आपके नाम पर खेती की जमीन है?"
            elif "is_income_tax_payer" in question_key:
                return "सरकारी नियमों की पुष्टि के लिए, क्या आपके परिवार में कोई इनकम टैक्स भरता है?"
            elif "monthly_income" in question_key:
                return "कृपया अपनी महीने की अनुमानित आमदनी (जैसे 10,000 से कम या अधिक) साझा करें।"
            elif "annual_income" in question_key:
                return "आपके पूरे परिवार की साल भर की कुल कमाई लगभग कितनी हो जाती है?"
            elif "covered_by_epfo_esic" in question_key:
                return "क्या आपका पीएफ कटता है या ईएसआईसी कार्ड है? कृपया 'हाँ' या 'नहीं' बताएं।"
            elif "has_crop_loss" in question_key:
                return "क्या हाल ही में सूखे या बेमौसम बारिश से आपकी फसल को 33% से अधिक नुकसान हुआ है?"
            return f"जी, आगे बढ़ने के लिए कृपया इसके बारे में थोड़ा और स्पष्ट बताएं।"
        elif language == "gu":
            if "occupation" in question_key:
                return "યોગ્ય યોજના શોધવા માટે, તમે મુખ્યત્વે ખેતી, મજૂરી, નાનો વેપાર કે નોકરી કરો છો તે જણાવો."
            elif "age" in question_key:
                return "કૃપા કરીને તમારી અંદાજિત ઉંમર જણાવો (દા.ત. 30 અથવા 45 વર્ષ) જેથી યોગ્ય યોજનાઓ મળી શકે."
            elif "owns_cultivable_land" in question_key or "land_acres" in question_key:
                return "ખાતરી કરવા માટે, શું તમારા નામે ખેતીની જમીન છે? 'હા' અથવા 'ના' માં જવાબ આપો."
            elif "is_income_tax_payer" in question_key:
                return "સરકારી નિયમોની ખાતરી માટે, શું તમારા પરિવારમાં કોઈ ઇન્કમટેક્સ ભરે છે?"
            elif "monthly_income" in question_key:
                return "કૃપા કરીને તમારી મહિનાની અંદાજિત આવક જણાવો."
            elif "annual_income" in question_key:
                return "તમારા પરિવારની વર્ષની કુલ આવક અંદાજે કેટલી છે?"
            elif "has_crop_loss" in question_key:
                return "શું દુષ્કાળ કે વરસાદથી તમારા પાકને 33% થી વધુ નુકસાન થયું છે?"
            return "આગળ વધવા માટે કૃપા કરીને આ વિગત સ્પષ્ટ જણાવો."
        elif language == "kn":
            if "occupation" in question_key:
                return (
                    "ಖಂಡಿತ. ನಿಖರವಾದ ಯೋಜನೆ ಹುಡುಕಲು, ನೀವು ಮುಖ್ಯವಾಗಿ ಕೃಷಿ, "
                    "ದಿನಗೂಲಿ ಕಾರ್ಮಿಕ, ಸ್ವಂತ ವ್ಯಾಪಾರ ಅಥವಾ ಉದ್ಯೋಗ ಮಾಡುತ್ತೀರಾ ಎಂದು ತಿಳಿಸಿ."
                )
            elif "age" in question_key:
                return "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಅಂದಾಜು ವಯಸ್ಸನ್ನು ತಿಳಿಸಿ (ಉದಾಹರಣೆಗೆ 30 ಅಥವಾ 45 ವರ್ಷ)."
            elif "owns_cultivable_land" in question_key or "land_acres" in question_key:
                return "ಖಚಿತಪಡಿಸಲು, ನಿಮ್ಮ ಕುಟುಂಬದ ಹೆಸರಿನಲ್ಲಿ ಕೃಷಿ ಭೂಮಿ ಇದೆಯೇ? 'ಹೌದು' ಅಥವಾ 'ಇಲ್ಲ' ಎಂದು ಉತ್ತರಿಸಿ."
            return "ಮುಂದುವರಿಯಲು, ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಸ್ಪಷ್ಟವಾಗಿ ತಿಳಿಸುವಿರಾ?"
        else:
            return f"Kindly share details regarding your {question_key.replace('_', ' ')} so we can find the matching scheme."


# Global instance of Indian Accent LLM Persona Engine
indian_accent_llm = IndianAccentLLM()
