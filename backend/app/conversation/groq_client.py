"""Groq LLM Client and Multilingual Language Analyzer for English, Hindi, and Gujarati."""

import json
import os
import re
from typing import Any

from dotenv import load_dotenv

from backend.app.core.logging import logger

load_dotenv()

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


class GroqEngine:
    """Handles Groq LLM integration, language detection, and slot extraction."""

    def __init__(self) -> None:
        self.client: Any = None
        self.reload_client()

    def reload_client(self) -> None:
        load_dotenv(override=True)
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        if HAS_GROQ and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info(f"Initialized Groq client with model: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")
                self.client = None
        else:
            self.client = None

    def is_available(self) -> bool:
        if self.client is None and os.getenv("GROQ_API_KEY"):
            self.reload_client()
        return self.client is not None

    def detect_language(self, text: str) -> str:
        """Classify user text as 'gu' (Gujarati), 'hi' (Hindi), or 'en' (English)."""
        if not text or not text.strip():
            return "en"

        cleaned = text.strip()

        # 1. Unicode Script Analysis
        gujarati_chars = len(re.findall(r"[\u0A80-\u0AFF]", cleaned))
        devanagari_chars = len(re.findall(r"[\u0900-\u097F]", cleaned))

        if gujarati_chars > 0 and gujarati_chars >= devanagari_chars:
            return "gu"
        if devanagari_chars > 0 and devanagari_chars > gujarati_chars:
            return "hi"

        # 2. If Groq LLM is available, leverage LLM classification for Romanized / code-mixed text
        if self.is_available():
            try:
                prompt = (
                    "You are a language detection classifier for India. "
                    "Analyze the given citizen statement and detect whether it is in 'en' (English), "
                    "'hi' (Hindi / Hinglish), or 'gu' (Gujarati / Gujarlish). "
                    "Respond with ONLY valid JSON: {\"language\": \"en\" | \"hi\" | \"gu\"}."
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": cleaned},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=60,
                    timeout=4.0,
                )
                content = response.choices[0].message.content or "{}"
                data = json.loads(content)
                detected = data.get("language", "").lower()
                if detected in ["en", "hi", "gu"]:
                    return detected
            except Exception as e:
                logger.debug(f"Groq language detection fallback to heuristic: {e}")

        # 3. Rule-based heuristic for Romanized Gujarati vs Hindi vs English
        lower_text = cleaned.lower()
        tokens = set(re.findall(r"\b[a-z]+\b", lower_text))

        gujarati_markers = {
            "khedut", "kheduto", "kheti", "jamin", "jamino", "varsad", "nuksan", "nuksaan",
            "maru", "mari", "maro", "tamari", "tamaro", "chhu", "chu", "chhe", "che", "tamne",
            "ekad", "ekar", "rupya", "aavaj", "kam", "madad", "sahaay", "sahay", "paak",
            "ummar", "vars", "varsh", "diyo", "aapvo", "gujarat", "gujarati",
        }

        english_markers = {
            "i", "am", "my", "we", "our", "you", "your", "is", "are", "was", "were",
            "have", "has", "had", "do", "does", "did", "what", "which", "who", "whom",
            "this", "that", "these", "those", "how", "much", "many", "give", "tell",
            "years", "old", "farmer", "worker", "income", "land", "rupees", "help",
            "scheme", "government", "assistance", "benefit", "need", "please", "can",
            "health", "cover", "hospital", "money", "apply", "form", "documents", "card",
        }

        hindi_markers = {
            "namaste", "pranam", "kheti", "majdoor", "mazdoor", "dihadi",
            "fasal", "sookh", "sukha", "barish", "baarish", "garbhwati", "bachha",
            "kamata", "kamai", "rupaye", "rupya", "mahina", "mahine", "meri", "mera", "mere",
            "umar", "umr", "saal", "varsh", "aay", "hai", "hain", "hu", "hoon", "nahi", "nahin",
            "chahiye", "madad", "sarkari",
        }

        en_overlap = len(tokens.intersection(english_markers))
        gu_overlap = len(tokens.intersection(gujarati_markers))
        hi_overlap = len(tokens.intersection(hindi_markers))

        if en_overlap > hi_overlap and en_overlap > gu_overlap:
            return "en"
        if gu_overlap > 0 and gu_overlap >= hi_overlap:
            return "gu"
        if hi_overlap > 0:
            return "hi"

        return "en"

    def style_reply_with_groq(
        self, user_text: str, base_reply: str, language: str = "en"
    ) -> str:
        """Use Groq LLM to make the response warm, natural, and concise in the citizen's language."""
        if not self.is_available() or not user_text.strip():
            return base_reply

        lang_names = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}
        target_name = lang_names.get(language, "Hindi")

        prompt = (
            f"You are Seva Vaani, a compassionate, respectful voice assistant for Indian welfare schemes. "
            f"Given the user's message and the system's required question or response, rephrase it in natural, "
            f"polite spoken {target_name}. "
            f"Requirements:\n"
            f"- Strictly 1 to 2 short sentences suitable for text-to-speech audio.\n"
            f"- Do NOT add any meta-announcements, do NOT mention Groq, LLM, or AI.\n"
            f"- Keep all required questions or options clear.\n"
            f"- Output ONLY the spoken response text, nothing else."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": f"User said: {user_text}\nSystem needs to say: {base_reply}",
                    },
                ],
                temperature=0.2,
                max_tokens=120,
                timeout=4.0,
            )
            styled = response.choices[0].message.content.strip()
            if styled and len(styled) < 300:
                return styled
        except Exception as e:
            logger.debug(f"Groq conversational styling fallback: {e}")

        return base_reply

    def format_groq_acknowledgment(self, language: str) -> str:
        """Deprecated: retained for backwards compatibility."""
        return ""

    def extract_slots_with_groq(
        self, text: str, current_facts: dict[str, Any], language: str = "en"
    ) -> dict[str, Any]:
        """Leverage Groq LLM to extract citizen demographic and eligibility slots."""
        if not self.is_available() or not text.strip():
            return {}

        prompt = (
            "You are an expert citizen intake assistant for Indian welfare schemes. "
            "Extract verified facts from the user's message. Output ONLY a valid JSON object.\n"
            "Allowed keys and formats:\n"
            "- age: integer (e.g. 35)\n"
            "- occupation: one of ['farmer', 'unorganized_worker', 'self_employed', 'salaried_govt', 'salaried_private', 'homemaker', 'student', 'artisan'] or null\n"
            "- owns_cultivable_land: boolean or null\n"
            "- land_acres: float or null\n"
            "- monthly_income: integer in INR or null\n"
            "- annual_income: integer in INR or null\n"
            "- is_income_tax_payer: boolean or null\n"
            "- covered_by_epfo_esic: boolean or null\n"
            "- is_pregnant_or_lactating: boolean or null\n"
            "- has_crop_loss: boolean or null\n"
            "- gender: 'male', 'female', 'other' or null\n"
            "- state_of_residence: string or null\n"
            "Only include keys that are explicitly mentioned or strongly implied. Do not guess."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": f"Language: {language}\nCurrent known facts: {json.dumps(current_facts)}\nCitizen text: {text}",
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=250,
                timeout=5.0,
            )
            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
            # Filter valid keys
            valid_keys = {
                "age", "occupation", "owns_cultivable_land", "land_acres",
                "monthly_income", "annual_income", "is_income_tax_payer",
                "covered_by_epfo_esic", "is_pregnant_or_lactating", "has_crop_loss",
                "gender", "state_of_residence"
            }
            return {k: v for k, v in data.items() if k in valid_keys and v is not None}
        except Exception as e:
            logger.warning(f"Groq slot extraction failed: {e}")
            return {}


    def clean_spoken_text(self, text: str) -> str:
        """Strip markdown markers and stray characters for pristine audio and display."""
        if not text:
            return ""
        cleaned = text.strip().strip('"').strip("'")
        cleaned = re.sub(r"[\*\_#`]", "", cleaned)
        cleaned = re.sub(r"[\U00010000-\U0010ffff]", "", cleaned)
        cleaned = re.sub(r" +", " ", cleaned).strip()
        return cleaned

    def generate_intake_reply(
        self,
        user_text: str,
        current_facts: dict[str, Any],
        next_question_key: str,
        next_question_text: str,
        options: list[str],
        language: str = "en",
    ) -> str:
        """Use Groq to answer citizen questions/concerns directly while asking the next required question."""
        if not self.is_available() or not user_text.strip():
            return ""

        target_name = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}.get(language, "Hindi")
        filtered_facts = {
            k: v for k, v in current_facts.items()
            if v is not None and not k.startswith("fact_")
        }

        system_prompt = (
            f"You are Seva Vaani, an empathetic voice assistant for Indian government welfare schemes. "
            f"You communicate warmly in {target_name}. "
            f"The citizen just said: '{user_text}'. "
            f"Known facts about the citizen: {json.dumps(filtered_facts)}. "
            f"Next required intake question: '{next_question_text}' (Topic: {next_question_key}). "
            f"Guidelines:\n"
            f"1. If the citizen asked a question, expressed doubt, or shared a hardship, answer them directly and helpfully in 1 sentence.\n"
            f"2. Then politely ask for the required detail ('{next_question_text}').\n"
            f"3. Strict length: 1 to 2 short spoken sentences total. Suitable for voice speech.\n"
            f"4. Never mention Groq, LLM, AI, prompt, or system. Never use emojis.\n"
            f"5. Output ONLY the spoken response."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.2,
                max_tokens=140,
                timeout=5.0,
            )
            reply = self.clean_spoken_text(response.choices[0].message.content or "")
            if reply and len(reply) < 320:
                return reply
        except Exception as e:
            logger.warning(f"Groq intake reply generation failed: {e}")

        return ""

    def generate_summary_reply(
        self,
        matched_schemes: list[Any],
        facts: dict[str, Any],
        language: str = "en",
    ) -> str:
        """Use Groq to generate a warm congratulations and eligibility summary in English, Hindi, or Gujarati."""
        if not self.is_available():
            return ""

        target_name = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}.get(language, "Hindi")
        scheme_summaries = []
        for s in matched_schemes:
            name = getattr(s, "scheme_name", str(s)).split("(")[0].strip()
            benefit = getattr(s, "benefit_summary", "")
            scheme_summaries.append(f"- {name}: {benefit}")
        schemes_text = "\n".join(scheme_summaries) if scheme_summaries else "Eligible welfare programs"

        system_prompt = (
            f"You are Seva Vaani, an empathetic voice assistant for Indian welfare schemes. "
            f"The citizen completed the intake. Based on verified government rules, they qualify for these schemes:\n"
            f"{schemes_text}\n\n"
            f"Deliver a warm, congratulatory summary in natural spoken {target_name}.\n"
            f"Guidelines:\n"
            f"1. Start with a warm congratulation (e.g. 'बधाई हो जी!' / 'અભિનંદન!' / 'Great news ji!').\n"
            f"2. State that based on their details, they qualify for {len(matched_schemes)} government scheme(s), highlighting top scheme names.\n"
            f"3. Inform them they can ask for details of any scheme or ask you to fill the application form for them.\n"
            f"4. Keep it strictly under 3 spoken sentences. No technical jargon, no AI/Groq mentions, no emojis.\n"
            f"5. Output ONLY the spoken response."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Please deliver the final eligibility outcome."},
                ],
                temperature=0.2,
                max_tokens=180,
                timeout=5.0,
            )
            reply = self.clean_spoken_text(response.choices[0].message.content or "")
            if reply and len(reply) < 380:
                return reply
        except Exception as e:
            logger.warning(f"Groq summary reply generation failed: {e}")

        return ""

    def generate_scheme_details_reply(
        self,
        user_text: str,
        scheme: Any,
        language: str = "en",
    ) -> str:
        """Use Groq to explain scheme benefits, required documents, and eligibility rules."""
        if not self.is_available():
            return ""

        target_name = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}.get(language, "Hindi")
        scheme_name = getattr(scheme, "scheme_name", str(scheme)).split("(")[0].strip()
        benefit = getattr(scheme, "benefit_summary", "Financial and welfare support")
        docs = getattr(scheme, "required_documents", ["Aadhaar Card", "Bank Passbook"])
        docs_str = ", ".join(docs[:4]) if isinstance(docs, list) else str(docs)

        system_prompt = (
            f"You are Seva Vaani, an expert voice assistant on Indian welfare schemes. "
            f"Scheme: {scheme_name}\n"
            f"Key Benefits (लाभ / લાભ): {benefit}\n"
            f"Required Documents (दस्तावेज / દસ્તાવેજ): {docs_str}\n\n"
            f"Citizen query: '{user_text}'.\n"
            f"Guidelines:\n"
            f"1. Answer their question directly in natural spoken {target_name}.\n"
            f"2. Clearly mention the key benefits ({benefit}) and required documents ({docs_str}).\n"
            f"3. Tell the citizen they can say 'fill form' (फॉर्म भरें / ફોર્મ ભરો) whenever they want to apply.\n"
            f"4. Keep response to 2 short spoken sentences. No emojis, no meta AI announcements.\n"
            f"5. Output ONLY the spoken text."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.2,
                max_tokens=160,
                timeout=5.0,
            )
            reply = self.clean_spoken_text(response.choices[0].message.content or "")
            if reply and len(reply) < 350:
                return reply
        except Exception as e:
            logger.warning(f"Groq scheme details reply generation failed: {e}")

        return ""

    def generate_form_fill_reply(
        self,
        user_text: str,
        scheme_name: str,
        facts: dict[str, Any],
        language: str = "en",
    ) -> str:
        """Use Groq to confirm that the official application form has been prepared and opened on screen."""
        if not self.is_available():
            return ""

        target_name = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}.get(language, "Hindi")
        facts_summary = []
        if facts.get("age"):
            facts_summary.append(f"age {facts['age']}")
        if facts.get("occupation"):
            facts_summary.append(f"occupation {facts['occupation']}")
        if facts.get("land_acres"):
            facts_summary.append(f"{facts['land_acres']} acres land")
        if facts.get("annual_income"):
            facts_summary.append(f"annual income {facts['annual_income']}")
        facts_str = ", ".join(facts_summary) or "verified profile"

        system_prompt = (
            f"You are Seva Vaani, an assistant helping Indian citizens apply for government schemes. "
            f"The citizen said: '{user_text}'.\n"
            f"Scheme to apply: {scheme_name}\n"
            f"Citizen's verified data: {facts_str}\n\n"
            f"Guidelines:\n"
            f"1. Confirm warmly in natural spoken {target_name} that you have prepared and opened the application form "
            f"(आवेदन फॉर्म / અરજી ફોર્મ / application form) using their verified details ({facts_str}).\n"
            f"2. Instruct them to review the form on their screen and click submit or confirm.\n"
            f"3. Strict length: 1 to 2 spoken sentences. No emojis, no mention of AI or Groq.\n"
            f"4. Output ONLY the spoken text."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.2,
                max_tokens=140,
                timeout=5.0,
            )
            reply = self.clean_spoken_text(response.choices[0].message.content or "")
            if reply and len(reply) < 320:
                return reply
        except Exception as e:
            logger.warning(f"Groq form fill reply generation failed: {e}")

        return ""

    def generate_general_query_reply(
        self,
        user_text: str,
        matched_schemes: list[Any],
        facts: dict[str, Any],
        language: str = "en",
    ) -> str:
        """Use Groq to answer any citizen question regarding welfare schemes, eligibility, or procedures."""
        if not self.is_available():
            return ""

        target_name = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}.get(language, "Hindi")
        scheme_names = [getattr(s, "scheme_name", str(s)).split("(")[0].strip() for s in matched_schemes]
        schemes_str = ", ".join(scheme_names) if scheme_names else "general Indian welfare schemes"

        system_prompt = (
            f"You are Seva Vaani, a helpful, polite voice assistant for Indian citizens. "
            f"The citizen is inquiring about: '{user_text}'. "
            f"Relevant eligible schemes: {schemes_str}. "
            f"Answer their query accurately and respectfully in natural spoken {target_name}.\n"
            f"Requirements:\n"
            f"1. Provide a direct, factual answer in 1 to 2 sentences.\n"
            f"2. Guide them that they can ask for scheme details or ask you to fill the application form.\n"
            f"3. Strict length: 2 short spoken sentences. No emojis, no mention of Groq/LLM/AI.\n"
            f"4. Output ONLY the spoken response."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.2,
                max_tokens=150,
                timeout=5.0,
            )
            reply = self.clean_spoken_text(response.choices[0].message.content or "")
            if reply and len(reply) < 320:
                return reply
        except Exception as e:
            logger.warning(f"Groq general query reply generation failed: {e}")

        return ""


    def answer_any_question(
        self,
        user_text: str,
        context: dict[str, Any] | None = None,
        language: str = "en",
    ) -> str:
        """Answer literally any question or inquiry the citizen asks with full reasoning and empathy."""
        if not self.is_available() or not user_text.strip():
            return ""

        target_name = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}.get(language, "Hindi")
        context_str = json.dumps(context) if context else "General Indian citizen inquiry"

        system_prompt = (
            f"You are Seva Vaani, an intelligent, empathetic voice assistant for Indian citizens. "
            f"You possess comprehensive knowledge of Indian government welfare schemes, agriculture, civic procedures, "
            f"documentation, public services, and general citizen inquiries. "
            f"The citizen is speaking in {target_name}. "
            f"Context: {context_str}\n\n"
            f"Citizen asks: '{user_text}'.\n"
            f"Guidelines:\n"
            f"1. Directly and helpfully answer their question in natural spoken {target_name}.\n"
            f"2. Length: 2 to 3 concise spoken sentences. Clear, practical, and conversational.\n"
            f"3. Never mention Groq, LLM, prompts, or system. Never use emojis.\n"
            f"4. Output ONLY the spoken response."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.3,
                max_tokens=220,
                timeout=6.0,
            )
            reply = self.clean_spoken_text(response.choices[0].message.content or "")
            if reply and len(reply) < 450:
                return reply
        except Exception as e:
            logger.warning(f"Groq open-ended answer generation failed: {e}")

        return ""


groq_engine = GroqEngine()
