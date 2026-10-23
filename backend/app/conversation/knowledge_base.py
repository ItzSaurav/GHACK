"""Comprehensive Civic Knowledge Base and Question-Answering Engine.
Provides authoritative, verified answers across English, Hindi, and Gujarati
for any citizen inquiry regarding government schemes, eligibility rules,
benefits, required documents, administrative procedures, and civic guidance.
"""

import re
from typing import Any

CIVIC_KNOWLEDGE_ENTRIES = [
    {
        "id": "pm_kisan_benefit",
        "patterns": [
            r"pm\s*kisan.*(paisa|rupaye|amount|benefit|labh|kitna|installment|kist|kitne)",
            r"pm\s*kisan.*(money|how much|financial)",
            r"(kisan|farmer).*(kitna|kitne).*(paisa|rupaye|milte|milega)",
            r"પીએમ\s*કિસાન.*(રૂપિયા|પૈસા|લાભ|કેટલા|હપ્તો)",
            r"प्रधानमंत्री\s*किसान.*(पैसे|रुपये|लाभ|कितना|कितने|किस्त)",
            r"6000.*(kab|milega|kisan)",
        ],
        "en": "Under PM-KISAN, eligible farmer families receive ₹6,000 per year directly in their bank accounts in three equal installments of ₹2,000 every four months through DBT.",
        "hi": "प्रधानमंत्री किसान सम्मान निधि (PM-KISAN) के तहत पात्र किसान परिवारों को प्रति वर्ष ₹6,000 की आर्थिक सहायता सीधे बैंक खाते में तीन 4-मासिक किस्तों (₹2,000 प्रत्येक) में डीबीटी द्वारा दी जाती है।",
        "gu": "પીએમ કિસાન યોજના હેઠળ પાત્ર ખેડૂત પરિવારોને વાર્ષિક ₹6,000 ની સહાય દર ચાર મહિને ₹2,000 ના ત્રણ સમાન હપ્તામાં સીધા બેંક ખાતામાં (DBT) જમા કરવામાં આવે છે.",
    },
    {
        "id": "pm_kisan_eligibility",
        "patterns": [
            r"pm\s*kisan.*(patra|eligib|criteria|kaun|apply|qualif|yogyata)",
            r"who is eligible.*(pm kisan|kisan samman)",
            r"કોણ\s*પાત્ર.*પીએમ\s*કિસાન",
            r"कौन\s*पात्र.*प्रधानमंत्री\s*किसान",
        ],
        "en": "All landholding farmer families with cultivable land in their names are eligible for PM-KISAN, provided they are not income tax payers, government employees, or institutional landholders.",
        "hi": "जिन किसान परिवारों के नाम पर कृषि योग्य भूमि है वे सभी पीएम-किसान के पात्र हैं, बशर्ते परिवार का कोई सदस्य इनकम टैक्स न भरता हो और सरकारी सेवा में न हो।",
        "gu": "જે ખેડૂત પરિવારના નામે ખેતીલાયક જમીન હોય તેઓ પીએમ કિસાન માટે પાત્ર છે, શરત કે તેઓ ઇન્કમટેક્સ ન ભરતા હોય કે સરકારી નોકરીમાં ન હોય.",
    },
    {
        "id": "pm_kisan_docs",
        "patterns": [
            r"pm\s*kisan.*(document|kagaz|dastawej|kaun se kagaj|proof)",
            r"documents.*(pm kisan|kisan scheme)",
            r"દસ્તાવેજ.*પીએમ\s*કિસાન",
            r"दस्तावेज.*प्रधानमंत्री\s*किसान",
        ],
        "en": "Required documents for PM-KISAN are: 1) Aadhaar Card, 2) Land Record / Khatauni (RoR 7/12 extract), 3) Bank Passbook linked with Aadhaar, and 4) Active Mobile number for eKYC.",
        "hi": "पीएम किसान के लिए आवश्यक दस्तावेज हैं: 1) आधार कार्ड, 2) जमीन के कागजात / खतौनी, 3) आधार से लिंक बैंक पासबुक, और 4) ई-केवाईसी के लिए मोबाइल नंबर।",
        "gu": "પીએમ કિસાન માટે જરૂરી દસ્તાવેજો: 1) આધાર કાર્ડ, 2) જમીનના કાગળો (7/12 અને 8-A), 3) આધાર લિંક કરેલ બેંક પાસબુક, અને 4) મોબાઈલ નંબર.",
    },
    {
        "id": "ayushman_benefit",
        "patterns": [
            r"(ayushman|pm\s*jay|jan arogya).*(benefit|cover|amount|paisa|kitna|labh|hospital|ilaj)",
            r"health cover.*(5 lakh|ayushman)",
            r"આયુષ્માન.*(લાભ|હોસ્પિટલ|કવર|કેટલા)",
            r"आयुष्मान.*(लाभ|इलाज|कवर|कितना|हॉस्पिटल)",
        ],
        "en": "Ayushman Bharat PM-JAY provides completely cashless hospital treatment cover of up to ₹5,00,000 per family per year for secondary and tertiary healthcare across empanelled public and private hospitals.",
        "hi": "आयुष्मान भारत (PM-JAY) के तहत प्रत्येक पात्र परिवार को सूचीबद्ध सरकारी व निजी अस्पतालों में गंभीर बीमारियों के इलाज के लिए प्रति वर्ष ₹5 लाख तक का निशुल्क कैशलेस स्वास्थ्य बीमा मिलता है।",
        "gu": "આયુષ્માન ભારત યોજના હેઠળ દરેક પાત્ર પરિવારને હોસ્પિટલમાં દાખલ થવા પર વાર્ષિક ₹5,00,000 સુધીની મફત કેશલેસ સારવાર સહાય મળે છે.",
    },
    {
        "id": "ayushman_senior_70",
        "patterns": [
            r"(70|senior citizen|buzurg|vridh|elderly).*(ayushman|pmjay|health)",
            r"70\s*वर्ष.*आयुष्मान",
            r"૭૦\s*વર્ષ.*આયુષ્માન",
        ],
        "en": "Under the expanded Ayushman Bharat scheme, all senior citizens aged 70 years and above receive universal health coverage of up to ₹5 Lakh per year, regardless of family income.",
        "hi": "विस्तारित आयुष्मान भारत योजना के तहत 70 वर्ष या उससे अधिक आयु के सभी वरिष्ठ नागरिकों को आय की सीमा के बिना प्रति वर्ष ₹5 लाख तक का निशुल्क स्वास्थ्य बीमा कवर मिलता है।",
        "gu": "વિસ્તૃત આયુષ્માન ભારત હેઠળ 70 વર્ષ કે તેથી વધુ ઉંમરના તમામ વરિષ્ઠ નાગરિકોને આવકની મર્યાદા વિના વાર્ષિક ₹5 લાખ સુધીનું મફત આરોગ્ય કવચ મળે છે.",
    },
    {
        "id": "pm_sym_pension",
        "patterns": [
            r"(shram yogi|pm\s*sym|maan\s*dhan|pmsym|majdoor pension).*(benefit|pension|kitna|amount|shramik)",
            r"unorganized.*pension.*(3000|shram)",
            r"શ્રમ\s*યોગી.*પેન્શન",
            r"श्रम\s*योगी.*पेंशन",
        ],
        "en": "PM Shram Yogi Maan-dhan provides an assured monthly pension of ₹3,000 after age 60 to unorganized workers (monthly income under ₹15,000, entry age 18-40) with a 50% matching government contribution.",
        "hi": "प्रधानमंत्री श्रम योगी मान-धन योजना असंगठित कामगारों (18-40 वर्ष, मासिक आय ₹15,000 से कम) को 60 वर्ष की आयु के बाद ₹3,000 प्रति माह की निश्चित पेंशन प्रदान करती है।",
        "gu": "પીએમ શ્રમ યોગી માનધન યોજના અસંગઠિત ક્ષેત્રના શ્રમિકોને 60 વર્ષની ઉંમર પછી ₹3,000 ની માસિક પેન્શન ખાતરીપૂર્વક આપે છે.",
    },
    {
        "id": "crop_disaster_relief",
        "patterns": [
            r"(crop loss|fasal nuksan|drought|flood|baarish|sukha|sukha rahat|disaster).*(relief|muavza|sahayata|compensation|madad)",
            r"पाક\s*નુકસાન.*(સહાય|વળતર|દુષ્કાળ|વરસાદ)",
            r"फसल\s*नुकसान.*(मुआवजा|राहत|सहायता|सूखा)",
        ],
        "en": "Under State Crop Disaster Relief and Mukhyamantri Kisan Sahayata, farmers who suffer more than 33% crop loss due to drought, unseasonal heavy rains, or pest attack receive direct compensation up to ₹20,000 per hectare.",
        "hi": "प्राकृतिक आपदा, सूखा या भारी बारिश से 33% से अधिक फसल नुकसान होने पर राज्य फसल आपदा राहत व मुख्यमंत्री किसान सहायता के तहत प्रति हेक्टेयर ₹20,000 तक की सीधी मुआवजा सहायता प्रदान की जाती है।",
        "gu": "દુષ્કાળ, કમોસમી વરસાદ કે કીટક પ્રકોપથી 33% થી વધુ પાક નુકસાન થાય તો રાજ્ય પાક આપદા સહાય હેઠળ હેક્ટર દીઠ ₹20,000 સુધીની સીધી વળતર સહાય મળે છે.",
    },
    {
        "id": "pmmvy_maternity",
        "patterns": [
            r"(matru vandana|pmmvy|pregnant|garbhvati|maternity|lactating).*(benefit|amount|paisa|madad)",
            r"ગર્ભવતી.*(સહાય|માતૃ\s*વંદના|રૂપિયા)",
            r"गर्भवती.*(सहायता|मातृत्व|मातृ\s*वंदना|पैसे)",
        ],
        "en": "Pradhan Mantri Matru Vandana Yojana (PMMVY) provides ₹5,000 in direct cash incentives for the first living child and ₹6,000 on the birth of a second girl child to support maternal health and nutrition.",
        "hi": "प्रधानमंत्री मातृ वंदना योजना (PMMVY) के तहत गर्भवती महिलाओं और स्तनपान कराने वाली माताओं को पहले बच्चे के लिए ₹5,000 और दूसरी कन्या संतान पर ₹6,000 की वित्तीय सहायता पोषण के लिए दी जाती है।",
        "gu": "પ્રધાનમંત્રી માતૃ વંદના યોજના હેઠળ સગર્ભા અને ધાત્રી માતાઓને પ્રથમ સંતાન માટે ₹5,000 અને બીજી દીકરીના જન્મ પર ₹6,000 ની સીધી આર્થિક સહાય પોષણ માટે આપવામાં આવે છે.",
    },
    {
        "id": "aadhaar_seeding_dbt",
        "patterns": [
            r"(aadhaar|adhar|dbt|npci|seed|link).*(bank|khata|account|kaise kare|link kaise)",
            r"how to link.*(aadhaar|bank|dbt)",
            r"આધાર.*(લિંક|બેંક|ખાતું|કેવી રીતે)",
            r"आधार.*(लिंक|सीडिंग|डीबीटी|बैंक खाता|कैसे करें)",
        ],
        "en": "To link Aadhaar with your bank account for DBT welfare payments, visit your home bank branch with your Aadhaar card and fill out the 'Aadhaar Seeding / Mandate Consent' form, or use your bank's mobile banking app.",
        "hi": "सरकारी योजनाओं की डीबीटी राशि पाने के लिए अपने आधार कार्ड की कॉपी लेकर बैंक शाखा जाएं और 'आधार सीडिंग / डीबीटी सहमति' फॉर्म भरें। आप बैंक के मोबाइल ऐप या नेट बैंकिंग से भी लिंक कर सकते हैं।",
        "gu": "ડીબીટી સહાય માટે આધાર કાર્ડને બેંક ખાતા સાથે લિંક કરવા બેંક શાખામાં જઈ 'આધાર સીડિંગ' ફોર્મ જમા કરો, અથવા નેટ બેંકિંગ/મોબાઈલ એપ્લિકેશન દ્વારા લિંક કરી શકાય છે.",
    },
    {
        "id": "csc_center_info",
        "patterns": [
            r"(csc|jan seva kendra|common service center|kendra).*(kahan|where|address|locate|kya hai)",
            r"જન\s*સેવા\s*કેન્દ્ર.*(ક્યાં|શું|મદદ)",
            r"जन\s*सेवा\s*केंद्र.*(कहाँ|क्या|सीएससी)",
        ],
        "en": "Common Service Centers (CSCs / Jan Seva Kendra) are village-level government assistance kiosks. You can locate your nearest CSC at your Gram Panchayat office or search online at findmycsc.nic.in.",
        "hi": "कॉमन सर्विस सेंटर (सीएससी / जन सेवा केंद्र) ग्राम पंचायत स्तर पर सरकारी सहायता केंद्र हैं। आप अपनी ग्राम पंचायत या findmycsc.nic.in पर जाकर नजदीकी केंद्र का पता लगा सकते हैं।",
        "gu": "કોમન સર્વિસ સેન્ટર (CSC / જન સેવા કેન્દ્ર) ગ્રામ પંચાયત સ્તરે સરકારી સેવાઓ માટે હોય છે. તમે તમારી ગ્રામ પંચાયત અથવા findmycsc.nic.in પરથી નજીકનું કેન્દ્ર શોધી શકો છો.",
    },
    {
        "id": "ekyc_procedure",
        "patterns": [
            r"(ekyc|e-kyc|kyc).*(kaise|procedure|pm kisan|how to)",
            r"ई-केवाईसी.*(कैसे|क्या)",
            r"કેવાયસી.*(કેવી રીતે)",
        ],
        "en": "For PM-KISAN eKYC, you can complete OTP-based eKYC free of cost on the pmkisan.gov.in portal using your Aadhaar-linked mobile number, or visit any CSC for biometric fingerprint eKYC.",
        "hi": "पीएम किसान ई-केवाईसी के लिए pmkisan.gov.in पोर्टल पर जाकर आधार से जुड़े मोबाइल नंबर से फ्री में ओटीपी ई-केवाईसी कर सकते हैं, या नजदीकी सीएससी जाकर फिंगरप्रिंट से बायोमेट्रिक ई-केवाईसी करा सकते हैं।",
        "gu": "પીએમ કિસાન ઈ-કેવાયસી માટે pmkisan.gov.in પર જઈ આધાર ઓટીપી દ્વારા ઘરે બેઠા મફતમાં કરી શકાય છે, અથવા નજીકના સીએસસી સેન્ટર પર બાયોમેટ્રિક ફિંગરપ્રિન્ટ દ્વારા કરાવી શકો છો.",
    },
    {
        "id": "assistant_identity",
        "patterns": [
            r"(who are you|tum kaun ho|aap kaun ho|who made you|your name|what do you do|kya kar sakte ho)",
            r"તમે\s*કોણ\s*છો",
            r"तुम\s*कौन\s*हो",
            r"आप\s*कौन\s*हैं",
        ],
        "en": "I am Seva Vaani, your dedicated voice assistant for Indian government welfare schemes. I help citizens discover eligible schemes, understand rules and benefits, and prefill application forms.",
        "hi": "मैं सेवा वाणी हूँ, भारत सरकार की कल्याणकारी योजनाओं के लिए आपकी आवाज़ सहायता। मैं आपकी सही योजनाएं खोजने, लाभ समझाने और फॉर्म भरने में पूरी मदद करती हूँ।",
        "gu": "હું સેવા વાણી છું, સરકારી કલ્યાણકારી યોજનાઓ માટે તમારી અંગત અવાજ સહાયક. હું તમને યોગ્ય યોજનાઓ શોધવામાં, લાભો સમજવામાં અને ફોર્મ ભરવામાં મદદ કરું છું.",
    },
    {
        "id": "jan_dhan_banking",
        "patterns": [
            r"(jan dhan|pmjdy|zero balance|bank account).*(open|kaise khole|benefit|khata)",
            r"જન\s*ધન.*ખાતું",
            r"जन\s*धन.*खाता",
        ],
        "en": "Pradhan Mantri Jan Dhan Yojana (PMJDY) offers zero-balance savings bank accounts with a free RuPay debit card, ₹2 Lakh accident insurance, and direct DBT transfer for government benefits.",
        "hi": "प्रधानमंत्री जन धन योजना (PMJDY) के तहत किसी भी बैंक में शून्य बैलेंस (जीरो बैलेंस) बचत खाता खुलवाया जा सकता है, जिसमें रुपे डेबिट कार्ड और ₹2 लाख का दुर्घटना बीमा मिलता है।",
        "gu": "પ્રધાનમંત્રી જન ધન યોજના હેઠળ કોઈપણ બેંકમાં ઝીરો બેલેન્સ ખાતું ખોલાવી શકાય છે, જેમાં મફત RuPay ડેબિટ કાર્ડ અને ₹2 લાખનો અકસ્માત વીમો મળે છે.",
    },
    {
        "id": "insurance_social_security",
        "patterns": [
            r"(bima|insurance|suraksha bima|jeevan jyoti|pmsby|pmjjby).*(kitna|premium|paisa)",
            r"વીમો.*(સુરક્ષા|જીવન\s*જ્યોતિ|પ્રીમિયમ)",
            r"बीमा.*(सुरक्षा बीमा|जीवन ज्योति|प्रीमियम)",
        ],
        "en": "PMSBY offers ₹2 Lakh accident insurance cover for just ₹20 per year. PMJJBY offers ₹2 Lakh life insurance cover for ₹436 per year. Both are auto-debited from your bank account.",
        "hi": "प्रधानमंत्री सुरक्षा बीमा योजना (PMSBY) केवल ₹20/वर्ष में ₹2 लाख का दुर्घटना बीमा देती है। प्रधानमंत्री जीवन ज्योति बीमा योजना (PMJJBY) ₹436/वर्ष में ₹2 लाख का जीवन बीमा देती है।",
        "gu": "પીએમ સુરક્ષા વીમા યોજના માત્ર ₹20/વર્ષમાં ₹2 લાખનો અકસ્માત વીમો આપે છે અને જીવન જ્યોતિ વીમા યોજના ₹436/વર્ષમાં ₹2 લાખનો જીવન વીમો આપે છે.",
    },
    {
        "id": "why_asking_facts",
        "patterns": [
            r"(why.*(asking|need)|kyu.*(puchh|chahiye)|kem.*(pucho|joie)).*(age|income|land|occupation|umar|kamai|jamin)",
            r"શા\s*માટે.*(ઉંમર|જમીન|આવક)",
            r"क्यों\s*पूछ.*(उम्र|जमीन|कमाई|आय)",
        ],
        "en": "Government welfare schemes have specific official eligibility criteria (such as farmer status, land size, age limits, and income brackets). These details ensure we accurately match only those schemes you legitimately qualify for.",
        "hi": "सरकारी योजनाओं के आधिकारिक नियम होते हैं (जैसे उम्र सीमा, जमीन का रकबा और आय सीमा)। आपकी दी गई जानकारी से हम केवल उन्हीं योजनाओं की पहचान करते हैं जिनके लिए आप वास्तविक रूप से पात्र हैं।",
        "gu": "સરકારી યોજનાઓમાં ચોક્કસ નિયમો (જેમ કે ઉંમરની મર્યાદા, જમીન અને આવક) હોય છે. આ વિગતોથી અમે ચોકસાઈપૂર્વક નક્કી કરી શકીએ છીએ કે તમે કઈ કઈ યોજના માટે પાત્ર છો.",
    },
]


class CivicKnowledgeEngine:
    """Matches citizen queries against authoritative knowledge entries."""

    def find_knowledge_answer(self, query: str, language: str = "en") -> str | None:
        if not query or not query.strip():
            return None

        clean_query = query.strip().lower()

        # Check each entry patterns
        for entry in CIVIC_KNOWLEDGE_ENTRIES:
            for pat in entry["patterns"]:
                if re.search(pat, clean_query, re.IGNORECASE):
                    if language == "gu":
                        return entry.get("gu") or entry.get("hi") or entry["en"]
                    elif language == "hi":
                        return entry.get("hi") or entry["en"]
                    else:
                        return entry["en"]

        return None

    def is_question_or_inquiry(self, text: str) -> bool:
        """Determines if the citizen statement contains an inquiry, question, or need for information."""
        if not text:
            return False
        clean = text.strip().lower()

        # Question mark
        if "?" in clean:
            return True

        # Common interrogatives across en, hi, gu
        question_words = [
            "what", "how", "why", "when", "where", "which", "who", "can i", "is there", "how much", "tell me",
            "kya", "kaise", "kyu", "kyun", "kab", "kahan", "kitna", "kitne", "kaun", "bataye", "batao", "bataiye", "milega",
            "shu", "kevi rite", "kem", "kyare", "kya", "ketla", "kon", "janavo", "kaho", "malshe", "aapo",
            "document", "dastawej", "kagaj", "patrata", "eligibility", "labh", "benefit",
        ]
        return any(re.search(rf"\b{re.escape(w)}\b", clean) for w in question_words)


civic_knowledge = CivicKnowledgeEngine()
