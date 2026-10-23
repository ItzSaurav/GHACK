import React, { useState, useEffect, useRef } from 'react';
import {
  ChatMessage,
  CitizenFacts,
  Language,
  SchemeEvaluationResult,
} from '../types';
import { api } from '../services/api';
import { useSpeech } from '../hooks/useSpeech';
import { VoiceInput } from '../components/VoiceInput';
import { QuestionCard } from '../components/QuestionCard';
import { SchemeResults } from '../components/SchemeResults';
import { FormModal } from '../components/FormModal';

interface SchemeAssistantWidgetProps {
  isOpen: boolean;
  onToggle: () => void;
  externalPrompt?: string | null;
  onClearExternalPrompt?: () => void;
}

export const LANGUAGE_OPTIONS: { code: Language; label: string }[] = [
  { code: 'en', label: 'English (IN)' },
  { code: 'hi', label: 'हिन्दी (Hindi)' },
  { code: 'gu', label: 'ગુજરાતી (Gujarati)' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'ta', label: 'தமிழ் (Tamil)' },
  { code: 'te', label: 'తెలుగు (Telugu)' },
  { code: 'ur', label: 'اردو (Urdu)' },
  { code: 'or', label: 'ଓଡ଼ିଆ (Odia)' },
  { code: 'mr', label: 'मराठी (Marathi)' },
  { code: 'ml', label: 'മലയാളം (Malayalam)' },
];

export const SchemeAssistantWidget: React.FC<SchemeAssistantWidgetProps> = ({
  isOpen,
  onToggle,
  externalPrompt,
  onClearExternalPrompt,
}) => {
  const [language, setLanguage] = useState<Language>('hi');
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [_currentQuestionKey, setCurrentQuestionKey] = useState<string | null>('age');
  const [currentOptions, setCurrentOptions] = useState<string[]>([]);
  const [_facts, setFacts] = useState<CitizenFacts>({});
  const [evaluationResults, setEvaluationResults] = useState<SchemeEvaluationResult[]>([]);
  const [isCompleted, setIsCompleted] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [activeFormScheme, setActiveFormScheme] = useState<SchemeEvaluationResult | null>(null);

  const [isHandsFreeLoop, setIsHandsFreeLoop] = useState(true);
  const isHandsFreeLoopRef = useRef(true);
  useEffect(() => {
    isHandsFreeLoopRef.current = isHandsFreeLoop;
  }, [isHandsFreeLoop]);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const onAudioCapturedRef = useRef<((blob: Blob) => Promise<void>) | null>(null);

  const {
    isListening,
    transcript,
    setTranscript,
    confidence,
    speechError,
    startListening,
    stopListening,
    isSpeaking,
    speechEnabled,
    setSpeechEnabled,
    speak,
    stopSpeaking,
    audioLevel,
    isUserSpeaking,
  } = useSpeech(language, {
    onAudioCaptured: (blob) => {
      if (onAudioCapturedRef.current) {
        onAudioCapturedRef.current(blob);
      }
    },
    onSpeechEnded: () => {
      if (isHandsFreeLoopRef.current && !isCompleted) {
        setTimeout(() => {
          startListening();
        }, 700);
      }
    },
  });

  const handleUserStartListening = () => {
    if (isSpeaking) {
      stopSpeaking();
    }
    startListening();
  };

  // Initialize conversation session on start
  const initSession = async (lang: Language) => {
    try {
      setIsBusy(true);
      const res = await api.startConversation(lang);
      setSessionId(res.session_id);
      setCurrentQuestionKey(res.current_question_key);
      setCurrentOptions(res.options);
      setMessages([
        {
          id: 'welcome-msg',
          role: 'assistant',
          text: res.greeting,
          source: 'system',
          timestamp: Date.now(),
        },
      ]);
      setFacts({});
      setEvaluationResults([]);
      setIsCompleted(false);
      setIsBusy(false);

      if (speechEnabled) {
        speak(res.greeting, lang);
      }
    } catch (err: any) {
      setIsBusy(false);
      setMessages([
        {
          id: 'error-msg',
          role: 'assistant',
          text:
            lang === 'gu'
              ? 'સર્વર સાથે જોડાવામાં સમસ્યા થઈ. કૃપા કરીને ફરી પ્રયાસ કરો.'
              : lang === 'hi'
              ? 'सर्वर से जुड़ने में समस्या हुई। कृपया पुनः प्रयास करें।'
              : 'Unable to connect to the backend assistant service. Please check your connection.',
          source: 'system',
          timestamp: Date.now(),
        },
      ]);
    }
  };

  const handleManualLanguageChange = (newLang: Language) => {
    setLanguage(newLang);
    initSession(newLang);
  };

  useEffect(() => {
    initSession(language);
  }, []);

  // Handle external prompts sent from the host portal (e.g., clicking "Ask Assistant about PM-KISAN")
  useEffect(() => {
    if (externalPrompt && sessionId && !isBusy) {
      handleSendMessage(externalPrompt, 'text');
      if (onClearExternalPrompt) {
        onClearExternalPrompt();
      }
    }
  }, [externalPrompt, sessionId]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (
    text: string,
    source: 'voice' | 'text' = 'text',
    audioConf?: number
  ) => {
    if (!text.trim() || !sessionId || isBusy) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text,
      source,
      audioConfidence: audioConf,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsBusy(true);

    try {
      const res = await api.sendMessage(sessionId, text, source, audioConf);

      const asstMsg: ChatMessage = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        text: res.reply,
        source: 'system',
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, asstMsg]);
      setCurrentQuestionKey(res.current_question_key);
      setCurrentOptions(res.options);
      setFacts(res.facts);
      setIsCompleted(res.is_completed);

      if (res.evaluation && res.evaluation.length > 0) {
        setEvaluationResults(res.evaluation);
      }

      if (res.open_form_scheme_id) {
        const schemeList = (res.evaluation && res.evaluation.length > 0)
          ? res.evaluation
          : evaluationResults;
        const target =
          schemeList.find(
            (s: SchemeEvaluationResult) => s.scheme_id === res.open_form_scheme_id
          ) || schemeList[0];
        if (target) {
          setActiveFormScheme(target);
        }
      }

      const targetLang =
        res.detected_language && ['en', 'hi', 'gu'].includes(res.detected_language)
          ? res.detected_language
          : language;

      if (
        res.detected_language &&
        res.detected_language !== language &&
        ['en', 'hi', 'gu'].includes(res.detected_language)
      ) {
        setLanguage(res.detected_language);
      }

      setIsBusy(false);

      if (speechEnabled) {
        speak(res.reply, targetLang);
      }
    } catch (err: any) {
      setIsBusy(false);
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          text:
            language === 'gu'
              ? 'ક્ષમા કરશો, સંદેશ પ્રક્રિયા કરવામાં ભૂલ આવી. કૃપા કરીને ફરી પ્રયાસ કરો.'
              : language === 'hi'
              ? 'क्षमा करें, संदेश संसाधित करने में त्रुटि हुई। कृपया पुनः प्रयास करें।'
              : 'Error processing message. Please retry.',
          source: 'system',
          timestamp: Date.now(),
        },
      ]);
    }
  };

  const handleUploadAudio = async (file: File | Blob) => {
    if (!sessionId || isBusy) return;
    setIsBusy(true);

    try {
      const res = await api.uploadVoice(sessionId, language, file);
      if (res.success && res.transcription?.text) {
        // Voice recognized
        const recognizedText = res.transcription.text;
        const conf = res.transcription.confidence;

        setMessages((prev) => [
          ...prev,
          {
            id: `voice-${Date.now()}`,
            role: 'user',
            text: recognizedText,
            source: 'voice',
            audioConfidence: conf,
            timestamp: Date.now(),
          },
        ]);

        if (res.dialogue_response) {
          const d = res.dialogue_response;
          setMessages((prev) => [
            ...prev,
            {
              id: `asst-${Date.now()}`,
              role: 'assistant',
              text: d.reply,
              source: 'system',
              timestamp: Date.now(),
            },
          ]);
          setCurrentQuestionKey(d.current_question_key);
          setCurrentOptions(d.options);
          setFacts(d.facts);
          setIsCompleted(d.is_completed);
          if (d.evaluation && d.evaluation.length > 0) {
            setEvaluationResults(d.evaluation);
          }

          if (d.open_form_scheme_id) {
            const schemeList = (d.evaluation && d.evaluation.length > 0)
              ? d.evaluation
              : evaluationResults;
            const target =
              schemeList.find(
                (s: SchemeEvaluationResult) => s.scheme_id === d.open_form_scheme_id
              ) || schemeList[0];
            if (target) {
              setActiveFormScheme(target);
            }
          }
          const targetLang =
            d.detected_language && ['en', 'hi', 'gu'].includes(d.detected_language)
              ? d.detected_language
              : language;
          if (
            d.detected_language &&
            d.detected_language !== language &&
            ['en', 'hi', 'gu'].includes(d.detected_language)
          ) {
            setLanguage(d.detected_language);
          }
          if (speechEnabled) {
            speak(d.reply, targetLang);
          }
        }
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: 'assistant',
            text:
              res.message ||
              (language === 'gu'
                ? 'અવાજ ઓળખાઈ શક્યો નહીં. કૃપા કરીને થોડું મોટેથી બોલો અથવા લખીને જવાબ આપો.'
                : language === 'hi'
                ? 'आवाज़ पहचानी नहीं जा सकी। कृपया थोड़ा तेज़ बोलें या लिखकर उत्तर दें।'
                : 'Could not recognize clear speech. Please speak louder or type your answer.'),
            source: 'system',
            timestamp: Date.now(),
          },
        ]);
      }
      setIsBusy(false);
    } catch (err: any) {
      setIsBusy(false);
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          text:
            language === 'gu'
              ? 'ઓડિયો પ્રક્રિયા કરવામાં ભૂલ આવી. કૃપા કરીને લખીને જવાબ આપો.'
              : language === 'hi'
              ? 'ऑडियो संसाधित करने में त्रुटि हुई। कृपया लिखकर उत्तर दें।'
              : (err.message || 'Audio upload failed.'),
          source: 'system',
          timestamp: Date.now(),
        },
      ]);
    }
  };

  useEffect(() => {
    onAudioCapturedRef.current = async (blob: Blob) => {
      if (transcript.trim() && (confidence ?? 0) >= 0.8) {
        handleSendMessage(transcript.trim(), 'voice', confidence ?? 0.85);
        setTranscript('');
      } else {
        await handleUploadAudio(blob);
      }
    };
  });

  const handleRestart = () => {
    stopSpeaking();
    initSession(language);
  };

  const handleEditAnswer = (text: string) => {
    setTranscript(text);
  };

  const getSuggestions = (): string[] => {
    if (currentOptions && currentOptions.length > 0) {
      return currentOptions.slice(0, 4);
    }
    if (language === 'gu') {
      return [
        'હું ૨ એકરનો નાનો ખેડૂત છું',
        'કોલેજ ફી સહાય જોઈએ છે',
        'ગુજરાત, રાજકોટ',
        'વાર્ષિક આવક ૭૫,૦૦૦',
      ];
    }
    if (language === 'hi') {
      return [
        '2 एकड़ के छोटे किसान',
        'कॉलेज फीस के लिए मदद',
        'कर्नाटक, धारवाड़',
        'सालाना आय 1.5 लाख',
      ];
    }
    return [
      'Small farmer with 2 acres',
      'College student fees help',
      'Karnataka, Dharwad',
      'Annual income 1.8 Lakhs',
    ];
  };

  return (
    <div className="sahaay-widget-root">
      {/* Embedded Assistant Panel / Drawer */}
      {isOpen && (
        <aside
          className="sahaay-widget-panel"
          role="complementary"
          aria-label="Government Scheme Assistant Widget"
        >
          {/* Widget Top Header */}
          <div className="widget-header">
            <div className="widget-header-brand">
              <span className="widget-badge-pill">VOICE</span>
              <span className="widget-title">
                {language === 'gu'
                  ? 'સેવા વાણી (Seva Vaani)'
                  : language === 'hi'
                  ? 'सेवा वाणी (Seva Vaani)'
                  : 'Seva Vaani'}
              </span>
              <span
                className="prototype-pill"
                style={{ padding: '0.1rem 0.4rem', fontSize: '0.625rem', backgroundColor: '#bc0100' }}
              >
                LIVE
              </span>
            </div>

            <div className="widget-header-actions">
              {/* Hands-free Conversation Loop Toggle */}
              <button
                type="button"
                className={`widget-tool-btn btn-loop-toggle ${isHandsFreeLoop ? 'active btn-loop-active' : ''}`}
                onClick={() => setIsHandsFreeLoop(!isHandsFreeLoop)}
                title={isHandsFreeLoop ? 'Hands-free conversational loop active' : 'Click to enable continuous voice conversation'}
                aria-label="Hands-free auto cycle toggle"
              >
                {isHandsFreeLoop ? 'Loop: ON' : 'Loop: OFF'}
              </button>

              {/* Voice Read-aloud toggle */}
              <button
                type="button"
                className={`widget-tool-btn ${speechEnabled ? 'active' : ''}`}
                onClick={() => setSpeechEnabled(!speechEnabled)}
                title={speechEnabled ? 'Mute voice read-aloud' : 'Enable voice read-aloud'}
                aria-label={speechEnabled ? 'Mute voice read-aloud' : 'Enable voice read-aloud'}
              >
                {speechEnabled ? 'Voice: ON' : 'Voice: OFF'}
              </button>

              {/* 10-Language Selector Dropdown */}
              <select
                className="widget-tool-btn widget-lang-select"
                value={language}
                onChange={(e) => handleManualLanguageChange(e.target.value as Language)}
                title="Select Assistant Language"
                aria-label="Select Assistant Language"
              >
                {LANGUAGE_OPTIONS.map((opt) => (
                  <option key={opt.code} value={opt.code}>
                    {opt.label}
                  </option>
                ))}
              </select>

              {/* Restart */}
              <button
                type="button"
                className="widget-tool-btn"
                onClick={handleRestart}
                title="Start Over"
              >
                Reset
              </button>

              {/* Close / Minimize */}
              <button
                type="button"
                className="widget-close-btn"
                onClick={onToggle}
                aria-label="Minimize assistant"
              >
                −
              </button>
            </div>
          </div>

          {/* Widget Conversation Scroll Area */}
          <div className="widget-body">
            <div className="messages-history">
              {messages.map((msg, index) => {
                const isLatestQuestion =
                  !isCompleted &&
                  index === messages.length - 1 &&
                  msg.role === 'assistant';

                if (msg.role === 'user') {
                  return (
                    <div key={msg.id} className="chat-bubble bubble-user">
                      <div className="bubble-header">
                        <span className="bubble-role">
                          {language === 'hi' ? 'आप' : 'You'}
                        </span>
                        <div className="bubble-user-meta">
                          <span className="match-pill">
                            <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>
                              check_circle
                            </span>
                            {msg.audioConfidence
                              ? `${Math.round(msg.audioConfidence * 100)}% match`
                              : '98% match'}
                          </span>
                          <button
                            type="button"
                            className="edit-answer-btn"
                            onClick={() => handleEditAnswer(msg.text)}
                            title="Edit this answer"
                          >
                            <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>
                              edit
                            </span>
                            {language === 'hi' ? 'सुधारें' : 'Edit answer'}
                          </button>
                        </div>
                      </div>
                      <p className="bubble-text">{msg.text}</p>
                    </div>
                  );
                }

                return (
                  <div
                    key={msg.id}
                    className={`chat-bubble bubble-assistant ${isLatestQuestion ? 'bubble-active-question' : ''}`}
                  >
                    <div className="bubble-header">
                      <span className="bubble-role">
                        <span className="bubble-assistant-avatar" aria-hidden="true">
                          <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>
                            smart_toy
                          </span>
                        </span>
                        {language === 'hi' ? 'सेवा वाणी' : 'Seva Vaani'}
                      </span>
                      {isLatestQuestion && (
                        <div className="active-question-badge-row">
                          <span className="active-question-pill">
                            {language === 'hi' ? 'सक्रिय प्रश्न' : 'Current Question'}
                          </span>
                          <button
                            type="button"
                            onClick={() => speak(msg.text, language)}
                            className="active-question-volume"
                            title="Read aloud"
                            aria-label="Read question aloud"
                            style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex' }}
                          >
                            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>
                              volume_up
                            </span>
                          </button>
                        </div>
                      )}
                    </div>
                    <p className="bubble-text">{msg.text}</p>
                  </div>
                );
              })}

              {isBusy && (
                <div className="chat-bubble bubble-assistant bubble-loading">
                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Current Active Question Card with Quick Options */}
            {messages.length > 0 && currentOptions && currentOptions.length > 0 && (
              <div className="widget-active-question-wrapper">
                <QuestionCard
                  language={language}
                  questionText={
                    messages[messages.length - 1]?.role === 'assistant'
                      ? messages[messages.length - 1].text
                      : 'Please provide the next detail.'
                  }
                  options={currentOptions}
                  onSelectOption={(opt) => handleSendMessage(opt, 'text')}
                  onSpeakAgain={() => {
                    const lastMsg = messages[messages.length - 1];
                    if (lastMsg && lastMsg.role === 'assistant') {
                      speak(lastMsg.text, language);
                    }
                  }}
                  isSpeaking={isSpeaking}
                  disabled={isBusy}
                />
              </div>
            )}

            {/* Scheme Eligibility Results View */}
            {evaluationResults.length > 0 && (
              <div className="widget-results-wrapper">
                <SchemeResults
                  language={language}
                  results={evaluationResults}
                  onStartFormAssistance={(scheme) => setActiveFormScheme(scheme)}
                />
              </div>
            )}
          </div>

          {/* Widget Voice & Text Input Dock */}
          <div className="widget-footer-dock">
            <VoiceInput
              language={language}
              isListening={isListening}
              audioLevel={audioLevel}
              isUserSpeaking={isUserSpeaking}
              transcript={transcript}
              onTranscriptChange={setTranscript}
              confidence={confidence}
              speechError={speechError}
              onStartListening={handleUserStartListening}
              onStopListening={stopListening}
              onSendMessage={handleSendMessage}
              onUploadAudioFile={handleUploadAudio}
              disabled={isBusy}
              suggestions={getSuggestions()}
              onSelectSuggestion={(sug) => handleSendMessage(sug, 'text')}
            />
          </div>
        </aside>
      )}

      {/* Form Assistance Modal */}
      {activeFormScheme && (
        <FormModal
          language={language}
          scheme={activeFormScheme}
          sessionId={sessionId}
          onClose={() => setActiveFormScheme(null)}
        />
      )}
    </div>
  );
};
