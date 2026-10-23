#include "groq_client.hpp"

#include <cassert>
#include <iostream>

using namespace voicebot;

void test_offline_fallback() {
    auto en_info = LanguageDetector::get_info(Language::English);
    auto en_reply = GroqClient::offline_fallback("hello", en_info);
    assert(!en_reply.empty());
    assert(en_reply.find("listening") != std::string::npos || en_reply.find("English") != std::string::npos);

    auto hi_info = LanguageDetector::get_info(Language::Hindi);
    auto hi_reply = GroqClient::offline_fallback("नमस्ते", hi_info);
    assert(!hi_reply.empty());
    assert(hi_reply.find("नमस्ते") != std::string::npos);

    auto gu_info = LanguageDetector::get_info(Language::Gujarati);
    auto gu_reply = GroqClient::offline_fallback("નમસ્તે", gu_info);
    assert(!gu_reply.empty());
    assert(gu_reply.find("નમસ્તે") != std::string::npos);

    auto mr_info = LanguageDetector::get_info(Language::Marathi);
    auto mr_reply = GroqClient::offline_fallback("नमस्कार", mr_info);
    assert(!mr_reply.empty());
    assert(mr_reply.find("नमस्कार") != std::string::npos);

    std::cout << "PASS: Offline fallback responses for all 4 languages passed\n";
}

void test_chat_fallback_routing() {
    GroqClient client;
    // Without API key, chat() should execute fallback smoothly
    std::vector<ChatMessage> history = {
        {"user", "નમસ્તે, મારે મદદ જોઈએ છે"}
    };

    ChatResult res = client.chat(history);
    assert(res.success);
    assert(res.language_info.code == "gu");
    assert(!res.reply.empty());

    std::cout << "PASS: Chat auto-detection and fallback routing passed\n";
}

int main() {
    std::cout << "Running GroqClient Unit Tests...\n";
    test_offline_fallback();
    test_chat_fallback_routing();
    std::cout << "All GroqClient unit tests passed successfully!\n";
    return 0;
}
