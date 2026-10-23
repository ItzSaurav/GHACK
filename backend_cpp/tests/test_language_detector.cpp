#include "language_detector.hpp"

#include <cassert>
#include <iostream>

using namespace voicebot;

void test_english_detection() {
    auto info1 = LanguageDetector::detect("Hello, what is the weather today?");
    assert(info1.code == "en");

    auto info2 = LanguageDetector::detect("Good morning! I want to check government schemes.");
    assert(info2.code == "en");
    std::cout << "PASS: English detection tests passed\n";
}

void test_hindi_detection() {
    auto info1 = LanguageDetector::detect("नमस्ते जी, मुझे बताइए कि आप कैसे मदद कर सकते हैं?");
    assert(info1.code == "hi");

    auto info2 = LanguageDetector::detect("मेरी आय 1 लाख से कम है और मैं खेती करता हूँ");
    assert(info2.code == "hi");
    std::cout << "PASS: Hindi detection tests passed\n";
}

void test_gujarati_detection() {
    auto info1 = LanguageDetector::detect("નમસ્તે, મને સહાય યોજના વિશે સંપૂર્ણ માહિતી આપો");
    assert(info1.code == "gu");

    auto info2 = LanguageDetector::detect("હું ખેતી કરું છું અને મારે ફોર્મ ભરવું છે");
    assert(info2.code == "gu");
    std::cout << "PASS: Gujarati detection tests passed\n";
}

void test_marathi_detection() {
    auto info1 = LanguageDetector::detect("नमस्कार, मला सरकारी योजनांची माहिती पाहिजे आहे");
    assert(info1.code == "mr");

    auto info2 = LanguageDetector::detect("तुम्ही मला मदत करू शकता का? माझे नाव रमेश आहे.");
    assert(info2.code == "mr");

    auto info3 = LanguageDetector::detect("शाळेत जाणाऱ्या मुलांसाठी काय योजना आहेत?");
    assert(info3.code == "mr");
    std::cout << "PASS: Marathi detection tests passed\n";
}

void test_whisper_normalization() {
    auto info_hi = LanguageDetector::normalize_whisper_lang("hindi", "नमस्ते");
    assert(info_hi.code == "hi");

    auto info_gu = LanguageDetector::normalize_whisper_lang("gujarati", "નમસ્તે");
    assert(info_gu.code == "gu");

    auto info_mr = LanguageDetector::normalize_whisper_lang("marathi", "नमस्कार");
    assert(info_mr.code == "mr");

    auto info_en = LanguageDetector::normalize_whisper_lang("english", "Hello");
    assert(info_en.code == "en");

    std::cout << "PASS: Whisper normalization tests passed\n";
}

int main() {
    std::cout << "Running LanguageDetector Unit Tests...\n";
    test_english_detection();
    test_hindi_detection();
    test_gujarati_detection();
    test_marathi_detection();
    test_whisper_normalization();
    std::cout << "All LanguageDetector unit tests passed successfully!\n";
    return 0;
}
