#include "language_detector.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <vector>

namespace voicebot {

namespace {

// Helper to convert string to lowercase ASCII
std::string to_lower_ascii(std::string_view sv) {
    std::string out;
    out.reserve(sv.size());
    for (char c : sv) {
        out.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
    }
    return out;
}

// UTF-8 decode helper: returns next codepoint and advances index
uint32_t next_codepoint(std::string_view sv, size_t& i) noexcept {
    if (i >= sv.size()) return 0;
    unsigned char c = static_cast<unsigned char>(sv[i]);
    if (c < 0x80) {
        i += 1;
        return c;
    } else if ((c & 0xE0) == 0xC0) {
        if (i + 1 >= sv.size()) { i = sv.size(); return 0; }
        uint32_t cp = ((c & 0x1F) << 6) | (static_cast<unsigned char>(sv[i + 1]) & 0x3F);
        i += 2;
        return cp;
    } else if ((c & 0xF0) == 0xE0) {
        if (i + 2 >= sv.size()) { i = sv.size(); return 0; }
        uint32_t cp = ((c & 0x0F) << 12) |
                      ((static_cast<unsigned char>(sv[i + 1]) & 0x3F) << 6) |
                      (static_cast<unsigned char>(sv[i + 2]) & 0x3F);
        i += 3;
        return cp;
    } else if ((c & 0xF8) == 0xF0) {
        if (i + 3 >= sv.size()) { i = sv.size(); return 0; }
        uint32_t cp = ((c & 0x07) << 18) |
                      ((static_cast<unsigned char>(sv[i + 1]) & 0x3F) << 12) |
                      ((static_cast<unsigned char>(sv[i + 2]) & 0x3F) << 6) |
                      (static_cast<unsigned char>(sv[i + 3]) & 0x3F);
        i += 4;
        return cp;
    }
    i += 1;
    return 0;
}

bool contains_word(std::string_view text, std::string_view word) {
    return text.find(word) != std::string_view::npos;
}

} // anonymous namespace

Language LanguageDetector::from_code(std::string_view code) noexcept {
    if (code == "en") return Language::English;
    if (code == "hi") return Language::Hindi;
    if (code == "gu") return Language::Gujarati;
    if (code == "mr") return Language::Marathi;
    return Language::Unknown;
}

std::string LanguageDetector::to_code(Language lang) noexcept {
    switch (lang) {
        case Language::English:  return "en";
        case Language::Hindi:    return "hi";
        case Language::Gujarati: return "gu";
        case Language::Marathi:  return "mr";
        default:                 return "en";
    }
}

LanguageInfo LanguageDetector::get_info(Language lang) noexcept {
    switch (lang) {
        case Language::English:
            return {Language::English, "en", "English", "en-IN"};
        case Language::Hindi:
            return {Language::Hindi, "hi", "हिन्दी (Hindi)", "hi-IN"};
        case Language::Gujarati:
            return {Language::Gujarati, "gu", "ગુજરાતી (Gujarati)", "gu-IN"};
        case Language::Marathi:
            return {Language::Marathi, "mr", "मराठी (Marathi)", "mr-IN"};
        default:
            return {Language::English, "en", "English", "en-IN"};
    }
}

LanguageInfo LanguageDetector::get_info(std::string_view code) noexcept {
    return get_info(from_code(code));
}

LanguageInfo LanguageDetector::detect(std::string_view text) noexcept {
    if (text.empty()) {
        return get_info(Language::English);
    }

    size_t gujarati_count = 0;
    size_t devanagari_count = 0;
    size_t latin_count = 0;
    bool has_marathi_lla = false;

    size_t idx = 0;
    while (idx < text.size()) {
        uint32_t cp = next_codepoint(text, idx);
        if (cp >= 0x0A80 && cp <= 0x0AFF) {
            gujarati_count++;
        } else if (cp >= 0x0900 && cp <= 0x097F) {
            devanagari_count++;
            if (cp == 0x0933) { // Marathi 'ळ'
                has_marathi_lla = true;
            }
        } else if ((cp >= 'a' && cp <= 'z') || (cp >= 'A' && cp <= 'Z')) {
            latin_count++;
        }
    }

    // Direct script check for Gujarati
    if (gujarati_count > 0 && gujarati_count >= devanagari_count && gujarati_count >= latin_count / 2) {
        return get_info(Language::Gujarati);
    }

    // Devanagari script: determine between Hindi and Marathi
    if (devanagari_count > 0 && devanagari_count >= latin_count / 2) {
        if (has_marathi_lla) {
            return get_info(Language::Marathi);
        }

        // Check lexical markers
        static const std::vector<std::string_view> marathi_markers = {
            "आहे", "आहेत", "नाही", "नाहीत", "काय", "कसे", "कशी", "करा", "करू",
            "तुम्ही", "माझे", "आपण", "होय", "सांगा", "पाहिजे", "झाले", "झाली",
            "मध्ये", "करायचे", "करायची", "नमस्कार", "धन्यवाद"
        };

        static const std::vector<std::string_view> hindi_markers = {
            "है", "हैं", "नहीं", "क्या", "कैसे", "कैसी", "करें", "करूं",
            "आप", "मेरा", "मेरी", "मेरे", "हाँ", "बताइए", "चाहिए", "हुआ",
            "हुई", "में", "पर", "नमस्ते", "शुक्रिया"
        };

        size_t mr_score = 0;
        for (const auto& marker : marathi_markers) {
            if (contains_word(text, marker)) mr_score += 2;
        }

        size_t hi_score = 0;
        for (const auto& marker : hindi_markers) {
            if (contains_word(text, marker)) hi_score += 2;
        }

        if (mr_score > hi_score) {
            return get_info(Language::Marathi);
        }
        return get_info(Language::Hindi);
    }

    // Default to English if Latin characters dominate or no indic scripts present
    return get_info(Language::English);
}

LanguageInfo LanguageDetector::normalize_whisper_lang(
    std::string_view whisper_lang,
    std::string_view transcribed_text
) noexcept {
    std::string lower = to_lower_ascii(whisper_lang);

    if (lower == "hi" || lower == "hindi") {
        // Also check if text has Marathi markers (Whisper sometimes tags Devanagari as Hindi)
        LanguageInfo text_info = detect(transcribed_text);
        if (text_info.lang == Language::Marathi) {
            return text_info;
        }
        return get_info(Language::Hindi);
    }
    if (lower == "gu" || lower == "gujarati") {
        return get_info(Language::Gujarati);
    }
    if (lower == "mr" || lower == "marathi") {
        return get_info(Language::Marathi);
    }
    if (lower == "en" || lower == "english") {
        return get_info(Language::English);
    }

    // Fallback to text detection if whisper language was unknown or generic
    return detect(transcribed_text);
}

} // namespace voicebot
