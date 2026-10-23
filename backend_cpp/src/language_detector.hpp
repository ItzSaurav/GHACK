#pragma once

#include <string>
#include <string_view>
#include <unordered_map>

namespace voicebot {

enum class Language {
    English,
    Hindi,
    Gujarati,
    Marathi,
    Unknown
};

struct LanguageInfo {
    Language lang = Language::Unknown;
    std::string code;         // "en", "hi", "gu", "mr"
    std::string display_name; // "English", "हिन्दी (Hindi)", "ગુજરાતી (Gujarati)", "मराठी (Marathi)"
    std::string bcp47;        // "en-IN", "hi-IN", "gu-IN", "mr-IN"
};

class LanguageDetector {
public:
    static Language from_code(std::string_view code) noexcept;
    static std::string to_code(Language lang) noexcept;
    static LanguageInfo get_info(Language lang) noexcept;
    static LanguageInfo get_info(std::string_view code) noexcept;

    // Detects language from text across the 4 supported languages
    static LanguageInfo detect(std::string_view text) noexcept;

    // Normalizes Groq / Whisper language identifier (e.g. "hindi", "gujarati", "marathi", "english", "en")
    static LanguageInfo normalize_whisper_lang(std::string_view whisper_lang, std::string_view transcribed_text) noexcept;
};

} // namespace voicebot
