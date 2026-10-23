#pragma once

#include "language_detector.hpp"

#include <string>
#include <vector>

namespace voicebot {

struct ChatMessage {
    std::string role;    // "system", "user", "assistant"
    std::string content;
};

struct TranscriptionResult {
    bool success = false;
    std::string text;
    LanguageInfo language_info;
    double duration = 0.0;
    std::string error;
};

struct ChatResult {
    bool success = false;
    std::string reply;
    LanguageInfo language_info;
    std::string model;
    std::string error;
};

class GroqClient {
public:
    GroqClient();
    ~GroqClient();

    // Prevent copies, allow move
    GroqClient(const GroqClient&) = delete;
    GroqClient& operator=(const GroqClient&) = delete;
    GroqClient(GroqClient&&) noexcept;
    GroqClient& operator=(GroqClient&&) noexcept;

    bool is_available() const noexcept;
    std::string get_api_key() const noexcept;
    void set_api_key(std::string key) noexcept;
    void reload_env() noexcept;

    // Transcribe audio using Groq Whisper (whisper-large-v3) with auto language detection
    TranscriptionResult transcribe(
        const std::string& audio_bytes,
        const std::string& filename = "audio.webm"
    );

    // Conversational response using Groq LLaMA (llama-3.3-70b-versatile)
    ChatResult chat(
        const std::vector<ChatMessage>& history,
        std::string_view target_language_code = "auto"
    );

    // Deterministic conversational fallback if Groq API is absent or offline
    static std::string offline_fallback(
        std::string_view prompt,
        const LanguageInfo& lang_info
    );

private:
    std::string api_key_;
    std::string model_ = "openai/gpt-oss-120b";
    std::string whisper_model_ = "whisper-large-v3";

    void load_api_key_from_env_or_file() noexcept;
};

} // namespace voicebot
