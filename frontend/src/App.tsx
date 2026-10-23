import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ConversationMessage, LanguageCode, ServerHealth, VoiceState } from './types';
import { voiceApi } from './services/voiceApi';
import { JevVoiceEngine, LANGUAGE_REGISTRY } from './services/jevVoice';
import { WaveformVisualizer } from './components/WaveformVisualizer';

export const App: React.FC = () => {
  const [messages, setMessages] = useState<ConversationMessage[]>([
    {
      id: 'welcome-1',
      role: 'assistant',
      content: 'Hello! I am your multilingual conversational voice assistant. Speak to me in English, Hindi, Gujarati, or Marathi, and I will automatically detect your language and respond.',
      detectedLanguage: 'en',
      languageName: 'English',
      bcp47: 'en-IN',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [autoListen, setAutoListen] = useState<boolean>(true);
  const [voiceOutputEnabled, setVoiceOutputEnabled] = useState<boolean>(true);
  const [activeLanguage, setActiveLanguage] = useState<LanguageCode>('en');
  const [inputText, setInputText] = useState<string>('');
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [health, setHealth] = useState<ServerHealth | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // References
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const recognitionRef = useRef<any>(null);
  const chatScrollRef = useRef<HTMLDivElement | null>(null);

  // Load server health on startup
  useEffect(() => {
    voiceApi
      .getHealth()
      .then((data) => setHealth(data))
      .catch((err) => {
        console.warn('Backend health check error:', err);
        setErrorMessage('Connecting to C++ Voicebot Server...');
      });
  }, []);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [messages, liveTranscript]);

  // Audio level analyzer
  const startAudioMeter = (stream: MediaStream) => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioCtx();
      audioContextRef.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      analyserRef.current = analyser;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        setAudioLevel(Math.min(1, avg / 128));
        animFrameRef.current = requestAnimationFrame(tick);
      };
      tick();
    } catch (e) {
      console.warn('Web Audio meter not available:', e);
    }
  };

  const stopAudioMeter = () => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setAudioLevel(0);
  };

  // Speak assistant message aloud
  const vocalize = useCallback(
    (text: string, bcp47: string) => {
      if (!voiceOutputEnabled) {
        setVoiceState('idle');
        return;
      }

      setVoiceState('speaking');
      JevVoiceEngine.speak(
        text,
        bcp47,
        () => setVoiceState('speaking'),
        () => {
          setVoiceState('idle');
          if (autoListen) {
            setTimeout(() => {
              startListening();
            }, 600);
          }
        },
        (err) => {
          console.warn('Speech synthesis notice:', err);
          setVoiceState('idle');
        }
      );
    },
    [voiceOutputEnabled, autoListen]
  );

  // Send textual query to backend
  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    // Fast Jev client-side preview
    const detectedPreview = JevVoiceEngine.detectLanguage(text);
    setActiveLanguage(detectedPreview.code);

    const userMsg: ConversationMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      detectedLanguage: detectedPreview.code,
      languageName: detectedPreview.name,
      bcp47: detectedPreview.bcp47,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInputText('');
    setLiveTranscript('');
    setVoiceState('processing');
    setErrorMessage(null);

    const historyPayload = newHistory.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const res = await voiceApi.sendChatMessage(text, historyPayload, 'auto');
      const assistantMsg: ConversationMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: res.reply,
        detectedLanguage: res.detected_language,
        languageName: res.language_name,
        bcp47: res.bcp47,
        model: res.model,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setActiveLanguage(res.detected_language);
      vocalize(res.reply, res.bcp47);
    } catch (err: any) {
      console.error('Chat failed:', err);
      setErrorMessage(err.message || 'Failed to get response');
      setVoiceState('idle');
    }
  };

  // Start voice recording
  const startListening = async () => {
    JevVoiceEngine.stopSpeaking();
    setErrorMessage(null);
    setLiveTranscript('');
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      startAudioMeter(stream);

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        stopAudioMeter();
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        if (audioBlob.size < 1000) {
          // Empty or tap
          setVoiceState('idle');
          return;
        }

        await processRecordedAudio(audioBlob);
      };

      recorder.start(250);
      setVoiceState('listening');

      // Setup optional Web Speech preview if supported
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const rec = new SpeechRecognition();
          rec.continuous = true;
          rec.interimResults = true;
          rec.onresult = (evt: any) => {
            let interim = '';
            for (let i = evt.resultIndex; i < evt.results.length; ++i) {
              interim += evt.results[i][0].transcript;
            }
            if (interim) {
              setLiveTranscript(interim);
              const preview = JevVoiceEngine.detectLanguage(interim);
              setActiveLanguage(preview.code);
            }
          };
          rec.start();
          recognitionRef.current = rec;
        } catch (e) {
          // Non-critical fallback
        }
      }
    } catch (err: any) {
      console.error('Microphone access denied or unavailable:', err);
      setErrorMessage('Microphone access denied. Please grant microphone permissions.');
      setVoiceState('idle');
    }
  };

  // Stop recording
  const stopListening = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      recognitionRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  };

  // Process recorded audio through C++ server & Groq
  const processRecordedAudio = async (blob: Blob) => {
    setVoiceState('processing');

    const historyPayload = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const res = await voiceApi.interactWithAudio(blob, historyPayload, 'recording.webm');

      if (!res.transcription || !res.transcription.trim()) {
        setVoiceState('idle');
        return;
      }

      const userMsg: ConversationMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: res.transcription,
        detectedLanguage: res.detected_language,
        languageName: res.language_name,
        bcp47: res.bcp47,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      const assistantMsg: ConversationMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: res.reply,
        detectedLanguage: res.detected_language,
        languageName: res.language_name,
        bcp47: res.bcp47,
        model: res.model,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setActiveLanguage(res.detected_language);
      setLiveTranscript('');
      vocalize(res.reply, res.bcp47);
    } catch (err: any) {
      console.error('Audio processing failed:', err);
      // Fallback: If text was captured via interim recognition, try sending text
      if (liveTranscript.trim()) {
        handleSendMessage(liveTranscript);
      } else {
        setErrorMessage(err.message || 'Voice transcription failed. Please try speaking again.');
        setVoiceState('idle');
      }
    }
  };

  const handleMicClick = () => {
    if (voiceState === 'listening') {
      stopListening();
    } else {
      startListening();
    }
  };

  const clearChat = () => {
    JevVoiceEngine.stopSpeaking();
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: 'Conversation cleared. Speak or type in English, Hindi, Gujarati, or Marathi to start.',
        detectedLanguage: 'en',
        languageName: 'English',
        bcp47: 'en-IN',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    setVoiceState('idle');
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-20 px-4 lg:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-lg text-white shadow-md shadow-blue-500/20">
            SV
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold text-slate-100 tracking-tight">Sahaay Voice</h1>
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-950 border border-emerald-800 text-emerald-400">
                {health?.engine || 'C++ Core Active'}
              </span>
              {health && (
                <span className={`px-2 py-0.5 rounded text-xs font-medium border ${
                  health.groq_available
                    ? 'bg-blue-950 border-blue-800 text-blue-400'
                    : 'bg-amber-950 border-amber-800 text-amber-400'
                }`}>
                  {health.groq_available ? 'Groq Active' : 'Fallback Ready'}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400">Multilingual Conversational AI (No Selector / Auto-Detect)</p>
          </div>
        </div>

        {/* Status Pills and Controls */}
        <div className="flex items-center gap-2.5 sm:gap-4">
          {/* Detected Language Pill */}
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700 text-xs">
            <span className="text-slate-400">Detected:</span>
            <span className="font-semibold text-blue-400">{LANGUAGE_REGISTRY[activeLanguage]?.name}</span>
          </div>

          {/* Auto-Listen Toggle */}
          <button
            onClick={() => setAutoListen(!autoListen)}
            title="Auto-Listen continues dialogue automatically after assistant answers"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              autoListen
                ? 'bg-blue-950/70 border-blue-700 text-blue-300'
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="material-symbols-outlined text-sm">
              {autoListen ? 'sync' : 'sync_disabled'}
            </span>
            <span className="hidden md:inline">Auto-Listen</span>
          </button>

          {/* Voice Output Toggle */}
          <button
            onClick={() => {
              if (voiceOutputEnabled) JevVoiceEngine.stopSpeaking();
              setVoiceOutputEnabled(!voiceOutputEnabled);
            }}
            title="Enable or mute assistant speech output"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              voiceOutputEnabled
                ? 'bg-emerald-950/70 border-emerald-700 text-emerald-300'
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="material-symbols-outlined text-sm">
              {voiceOutputEnabled ? 'volume_up' : 'volume_off'}
            </span>
            <span className="hidden md:inline">{voiceOutputEnabled ? 'Voice ON' : 'Muted'}</span>
          </button>

          {/* Clear Chat */}
          <button
            onClick={clearChat}
            title="Clear conversation"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-transparent transition-colors"
          >
            <span className="material-symbols-outlined text-base">delete_sweep</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 flex flex-col justify-between gap-4">
        {/* Error notification banner */}
        {errorMessage && (
          <div className="bg-amber-950/60 border border-amber-800/80 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-amber-300 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-base">warning</span>
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-amber-400 hover:text-amber-200 text-xs font-semibold"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Voice Interaction Stage */}
        <section className="bg-slate-950 border border-slate-800 rounded-2xl p-6 sm:p-8 flex flex-col items-center justify-center relative overflow-hidden shadow-xl">
          {/* Decorative glowing gradient ring */}
          <div
            className={`absolute w-72 h-72 rounded-full blur-3xl opacity-20 pointer-events-none transition-colors duration-500 ${
              voiceState === 'listening'
                ? 'bg-red-500'
                : voiceState === 'speaking'
                ? 'bg-blue-500'
                : voiceState === 'processing'
                ? 'bg-amber-500'
                : 'bg-blue-600'
            }`}
          />

          {/* Interactive Mic Orb */}
          <div className="relative mb-4">
            <button
              onClick={handleMicClick}
              disabled={voiceState === 'processing'}
              className={`w-28 h-28 sm:w-32 sm:h-32 rounded-full flex flex-col items-center justify-center transition-all duration-200 select-none shadow-2xl relative z-10 ${
                voiceState === 'listening'
                  ? 'bg-red-600 hover:bg-red-700 text-white ring-8 ring-red-500/20 scale-105 animate-pulse'
                  : voiceState === 'speaking'
                  ? 'bg-blue-600 text-white ring-8 ring-blue-500/20'
                  : voiceState === 'processing'
                  ? 'bg-amber-600 text-white ring-8 ring-amber-500/20 cursor-wait'
                  : 'bg-gradient-to-tr from-blue-700 to-indigo-600 hover:from-blue-600 hover:to-indigo-500 text-white ring-4 ring-blue-500/10 hover:scale-105'
              }`}
            >
              <span className="material-symbols-outlined text-4xl sm:text-5xl">
                {voiceState === 'listening'
                  ? 'stop'
                  : voiceState === 'processing'
                  ? 'hourglass_empty'
                  : voiceState === 'speaking'
                  ? 'record_voice_over'
                  : 'mic'}
              </span>
              <span className="text-[11px] font-semibold mt-1 tracking-wider uppercase opacity-90">
                {voiceState === 'listening'
                  ? 'Stop'
                  : voiceState === 'processing'
                  ? 'Thinking'
                  : voiceState === 'speaking'
                  ? 'Speaking'
                  : 'Speak'}
              </span>
            </button>
          </div>

          {/* State Text & Waveform */}
          <div className="text-center z-10 w-full max-w-md">
            <h2 className="text-base sm:text-lg font-semibold text-slate-100">
              {voiceState === 'listening' && 'Listening... Speak in any of the 4 languages'}
              {voiceState === 'processing' && 'Transcribing with Groq & generating response...'}
              {voiceState === 'speaking' && 'Speaking back...'}
              {voiceState === 'idle' && 'Tap the microphone and start speaking'}
              {voiceState === 'error' && 'Something went wrong. Please tap to try again'}
            </h2>

            {/* Audio Waveform */}
            <WaveformVisualizer state={voiceState} audioLevel={audioLevel} />

            {/* Live recognized preview */}
            {liveTranscript && (
              <p className="text-xs sm:text-sm text-blue-300 italic bg-blue-950/40 border border-blue-900/50 rounded-lg px-3 py-1.5 mt-1">
                "{liveTranscript}"
              </p>
            )}

            <p className="text-xs text-slate-400 mt-2">
              Supported languages: <strong className="text-slate-300">English</strong>,{' '}
              <strong className="text-slate-300">हिन्दी</strong>,{' '}
              <strong className="text-slate-300">ગુજરાતી</strong>,{' '}
              <strong className="text-slate-300">मराठी</strong> (Auto-Detected)
            </p>
          </div>
        </section>

        {/* Quick Starters in all 4 languages */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <button
            onClick={() => handleSendMessage('Hello! What can you help me with?')}
            className="p-2.5 rounded-xl bg-slate-950/60 hover:bg-slate-800 border border-slate-800 text-left transition-colors flex flex-col gap-1"
          >
            <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider">English</span>
            <span className="text-slate-300 line-clamp-1">What can you help with?</span>
          </button>

          <button
            onClick={() => handleSendMessage('नमस्ते जी, आप मेरे लिए क्या कर सकते हैं?')}
            className="p-2.5 rounded-xl bg-slate-950/60 hover:bg-slate-800 border border-slate-800 text-left transition-colors flex flex-col gap-1"
          >
            <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">हिन्दी</span>
            <span className="text-slate-300 line-clamp-1">आप मेरे लिए क्या कर सकते हैं?</span>
          </button>

          <button
            onClick={() => handleSendMessage('નમસ્તે, તમે કઈ કઈ ભાષા બોલી શકો છો?')}
            className="p-2.5 rounded-xl bg-slate-950/60 hover:bg-slate-800 border border-slate-800 text-left transition-colors flex flex-col gap-1"
          >
            <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">ગુજરાતી</span>
            <span className="text-slate-300 line-clamp-1">તમે કઈ ભાષા બોલી શકો છો?</span>
          </button>

          <button
            onClick={() => handleSendMessage('नमस्कार, मला तुमच्याबद्दल अधिक माहिती सांगा.')}
            className="p-2.5 rounded-xl bg-slate-950/60 hover:bg-slate-800 border border-slate-800 text-left transition-colors flex flex-col gap-1"
          >
            <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">मराठी</span>
            <span className="text-slate-300 line-clamp-1">मला अधिक माहिती सांगा</span>
          </button>
        </div>

        {/* Conversation Thread */}
        <section className="flex-1 bg-slate-950/60 border border-slate-800/80 rounded-2xl flex flex-col min-h-[280px] max-h-[460px] overflow-hidden shadow-inner">
          <div className="px-4 py-2.5 border-b border-slate-800/80 bg-slate-950/80 flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Live Dialogue</span>
            <span>{messages.length} messages</span>
          </div>

          <div ref={chatScrollRef} className="flex-1 p-4 overflow-y-auto space-y-3.5 custom-scroll">
            {messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
                >
                  <div className="flex items-center gap-1.5 mb-1 px-1 text-[11px] text-slate-400">
                    <span className="font-semibold text-slate-300">{isUser ? 'You' : 'Assistant'}</span>
                    {msg.detectedLanguage && (
                      <span className="px-1.5 py-0.2 rounded bg-slate-800 border border-slate-700 text-[10px] text-blue-300 font-mono">
                        {msg.languageName || msg.detectedLanguage}
                      </span>
                    )}
                    <span>{msg.timestamp}</span>
                  </div>

                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                      isUser
                        ? 'bg-blue-600 text-white rounded-br-none shadow-md shadow-blue-600/10'
                        : 'bg-slate-800/90 text-slate-100 rounded-bl-none border border-slate-700/80 shadow-md'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>

                    {!isUser && (
                      <div className="mt-2 pt-1.5 border-t border-slate-700/60 flex items-center justify-between text-[11px] text-slate-400">
                        <span className="text-[10px] font-mono text-slate-500">
                          {msg.model || 'Groq Core'}
                        </span>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => msg.bcp47 && vocalize(msg.content, msg.bcp47)}
                            className="flex items-center gap-1 text-slate-400 hover:text-blue-400 transition-colors"
                            title="Replay Voice"
                          >
                            <span className="material-symbols-outlined text-xs">volume_up</span>
                            <span>Play</span>
                          </button>
                          <button
                            onClick={() => navigator.clipboard.writeText(msg.content)}
                            className="flex items-center gap-1 text-slate-400 hover:text-blue-400 transition-colors"
                            title="Copy text"
                          >
                            <span className="material-symbols-outlined text-xs">content_copy</span>
                            <span>Copy</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Text Input Fallback Bar */}
          <div className="p-3 border-t border-slate-800/80 bg-slate-950/90 flex items-center gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSendMessage(inputText);
              }}
              placeholder="Or type a question in English, हिन्दी, ગુજરાતી, or मराठी..."
              className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
            />
            <button
              onClick={() => handleSendMessage(inputText)}
              disabled={!inputText.trim() || voiceState === 'processing'}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium transition-colors flex items-center gap-1.5"
            >
              <span className="material-symbols-outlined text-base">send</span>
              <span className="hidden sm:inline">Send</span>
            </button>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/60 px-4 py-3 text-center text-xs text-slate-500">
        High-Performance C++20 Server &bull; Groq LLaMA 3.3 &bull; Whisper Multi-Language Voice Engine
      </footer>
    </div>
  );
};

export default App;
