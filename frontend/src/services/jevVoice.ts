import { LanguageCode, LanguageInfo } from '../types';

export const LANGUAGE_REGISTRY: Record<LanguageCode, LanguageInfo> = {
  en: { code: 'en', name: 'English', bcp47: 'en-IN' },
  hi: { code: 'hi', name: 'हिन्दी (Hindi)', bcp47: 'hi-IN' },
  gu: { code: 'gu', name: 'ગુજરાતી (Gujarati)', bcp47: 'gu-IN' },
  mr: { code: 'mr', name: 'मराठी (Marathi)', bcp47: 'mr-IN' },
};

export class JevVoiceEngine {
  /**
   * Fast client-side language classifier using Unicode code-points and lexical tokens.
   */
  static detectLanguage(text: string): LanguageInfo {
    if (!text || text.trim().length === 0) {
      return LANGUAGE_REGISTRY.en;
    }

    let gujarati = 0;
    let devanagari = 0;
    let latin = 0;
    let hasMarathiLla = false;

    for (const char of text) {
      const code = char.charCodeAt(0);
      if (code >= 0x0a80 && code <= 0x0aff) {
        gujarati++;
      } else if (code >= 0x0900 && code <= 0x097f) {
        devanagari++;
        if (code === 0x0933) {
          hasMarathiLla = true;
        }
      } else if ((code >= 65 && code <= 90) || (code >= 97 && code <= 122)) {
        latin++;
      }
    }

    if (gujarati > 0 && gujarati >= devanagari && gujarati >= latin / 2) {
      return LANGUAGE_REGISTRY.gu;
    }

    if (devanagari > 0 && devanagari >= latin / 2) {
      if (hasMarathiLla) {
        return LANGUAGE_REGISTRY.mr;
      }

      const marathiTokens = [
        'आहे', 'आहेत', 'नाही', 'नाहीत', 'काय', 'कसे', 'कशी', 'करा', 'करू',
        'तुम्ही', 'माझे', 'आपण', 'होय', 'सांगा', 'पाहिजे', 'झाले', 'झाली', 'नमस्कार'
      ];
      const hindiTokens = [
        'है', 'हैं', 'नहीं', 'क्या', 'कैसे', 'कैसी', 'करें', 'करूं',
        'आप', 'मेरा', 'मेरी', 'मेरे', 'हाँ', 'बताइए', 'चाहिए', 'हुआ', 'हुई', 'नमस्ते'
      ];

      let mrScore = 0;
      for (const tok of marathiTokens) {
        if (text.includes(tok)) mrScore += 2;
      }

      let hiScore = 0;
      for (const tok of hindiTokens) {
        if (text.includes(tok)) hiScore += 2;
      }

      if (mrScore > hiScore) {
        return LANGUAGE_REGISTRY.mr;
      }
      return LANGUAGE_REGISTRY.hi;
    }

    return LANGUAGE_REGISTRY.en;
  }

  /**
   * Speak response using Web Speech Synthesis.
   */
  static speak(
    text: string,
    bcp47: string,
    onStart?: () => void,
    onEnd?: () => void,
    onError?: (err: any) => void
  ): SpeechSynthesisUtterance | null {
    if (!('speechSynthesis' in window)) {
      if (onEnd) onEnd();
      return null;
    }

    window.speechSynthesis.cancel();

    // Clean text of asterisks or markdown artifacts before speaking
    const cleanText = text
      .replace(/[*_#`~]/g, '')
      .replace(/\n+/g, ' ')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = bcp47;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    // Pick best matching voice if available
    const voices = window.speechSynthesis.getVoices();
    const primaryLang = bcp47.split('-')[0];
    const matchedVoice =
      voices.find((v) => v.lang.toLowerCase() === bcp47.toLowerCase()) ||
      voices.find((v) => v.lang.toLowerCase().startsWith(primaryLang)) ||
      voices.find((v) => v.lang.includes('IN'));

    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.onstart = () => {
      if (onStart) onStart();
    };

    utterance.onend = () => {
      if (onEnd) onEnd();
    };

    utterance.onerror = (e) => {
      if (onError) onError(e);
      if (onEnd) onEnd();
    };

    window.speechSynthesis.speak(utterance);
    return utterance;
  }

  static stopSpeaking(): void {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }
}
