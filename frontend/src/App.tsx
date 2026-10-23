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
      content:
        'नमस्ते! सेवा वाणी में आपका स्वागत है। आप मुझसे हिन्दी, ગુજરાતી, मराठी या English में बात कर सकते हैं। अपनी आवश्यकता या समस्या बताएं, भाषा स्वतः पहचानी जाएगी और आपको बोलकर उत्तर दिया जाएगा।',
      detectedLanguage: 'hi',
      languageName: 'हिन्दी (Hindi)',
      bcp47: 'hi-IN',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [autoListen, setAutoListen] = useState<boolean>(true);
  const [voiceOutputEnabled, setVoiceOutputEnabled] = useState<boolean>(true);
  const [activeLanguage, setActiveLanguage] = useState<LanguageCode>('hi');
  const [inputText, setInputText] = useState<string>('');
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [health, setHealth] = useState<ServerHealth | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fontSizeOffset, setFontSizeOffset] = useState<number>(0); // -1, 0, 1 for A-, A, A+

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

  // Speak assistant message aloud using Neural Audio with Web Speech fallback
  const vocalize = useCallback(
    (text: string, langCode: string) => {
      if (!voiceOutputEnabled) {
        setVoiceState('idle');
        return;
      }

      setVoiceState('speaking');
      JevVoiceEngine.playAudio(
        text,
        langCode,
        () => setVoiceState('speaking'),
        () => {
          setVoiceState('idle');
          if (autoListen) {
            setTimeout(() => {
              startListening();
            }, 800);
          }
        },
        (err) => {
          console.warn('Speech playback notice:', err);
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
      vocalize(res.reply, res.detected_language);
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
          setVoiceState('idle');
          return;
        }

        await processRecordedAudio(audioBlob);
      };

      recorder.start(250);
      setVoiceState('listening');

      // Web Speech recognition for interim live feedback preview
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
          // Web speech preview non-critical
        }
      }
    } catch (err: any) {
      console.error('Microphone access denied:', err);
      setErrorMessage('Microphone access denied. Please grant microphone permissions in browser.');
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
      vocalize(res.reply, res.detected_language);
    } catch (err: any) {
      console.error('Audio processing failed:', err);
      if (liveTranscript.trim()) {
        handleSendMessage(liveTranscript);
      } else {
        setErrorMessage(err.message || 'Voice transcription failed. Please speak again.');
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
        content:
          'संवाद साफ़ किया गया। आप किसी भी समय हिन्दी, ગુજરાતી, मराठी या English में बोलना या लिखना शुरू कर सकते हैं।',
        detectedLanguage: 'hi',
        languageName: 'हिन्दी (Hindi)',
        bcp47: 'hi-IN',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    setVoiceState('idle');
  };

  const rootFontSizeClass =
    fontSizeOffset === 1 ? 'text-[17px]' : fontSizeOffset === -1 ? 'text-[14px]' : 'text-[15px]';

  return (
    <div className={`min-h-screen bg-[#f4f6f9] text-[#1e293b] flex flex-col font-sans ${rootFontSizeClass}`}>
      {/* 1. Indian National Flag Top Accent Stripe */}
      <div
        className="h-1.5 w-full sticky top-0 z-50"
        style={{
          background: 'linear-gradient(to right, #FF9933 33.33%, #FFFFFF 33.33%, #FFFFFF 66.66%, #138808 66.66%)',
        }}
      />

      {/* 2. Official Government of India Top Utility Bar */}
      <div className="bg-[#0c2340] text-[#e2e8f0] text-xs px-4 sm:px-8 py-1.5 border-b border-[#163155] flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <span className="font-semibold tracking-wide flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#FF9933] inline-block" />
            भारत सरकार | Government of India
          </span>
          <span className="hidden md:inline text-slate-400">|</span>
          <span className="hidden md:inline text-slate-300">राष्ट्रीय नागरिक संवाद मंच</span>
        </div>

        {/* Accessibility & Language Auto-Detect Status */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 text-[11px] bg-[#163155] border border-[#234574] px-2.5 py-0.5 rounded text-amber-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Language Auto-Detect: Active (English / हिन्दी / ગુજરાતી / मराठी)</span>
          </div>

          <div className="hidden sm:flex items-center gap-1 border-l border-slate-700 pl-3">
            <button
              onClick={() => setFontSizeOffset(-1)}
              className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                fontSizeOffset === -1 ? 'bg-blue-600 text-white' : 'text-slate-300 hover:text-white'
              }`}
              title="Decrease text size"
            >
              A-
            </button>
            <button
              onClick={() => setFontSizeOffset(0)}
              className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                fontSizeOffset === 0 ? 'bg-blue-600 text-white' : 'text-slate-300 hover:text-white'
              }`}
              title="Normal text size"
            >
              A
            </button>
            <button
              onClick={() => setFontSizeOffset(1)}
              className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                fontSizeOffset === 1 ? 'bg-blue-600 text-white' : 'text-slate-300 hover:text-white'
              }`}
              title="Increase text size"
            >
              A+
            </button>
          </div>
        </div>
      </div>

      {/* 3. Official India.gov.in Main Header */}
      <header className="bg-white border-b border-slate-200 px-4 sm:px-8 py-3.5 shadow-sm">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-4">
          {/* State Emblem & Bilingual Portal Title */}
          <div className="flex items-center gap-3.5">
            {/* Ashoka Stambh Emblem Emblem Recreation */}
            <div className="flex flex-col items-center justify-center p-1 bg-amber-50/60 border border-amber-200/80 rounded-lg">
              <svg className="w-10 h-10 text-[#0c2340]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 1.5c4.69 0 8.5 3.81 8.5 8.5S16.69 20.5 12 20.5 3.5 16.69 3.5 12 7.31 3.5 12 3.5zm-1 3.5v5.25l4.5 2.67-.75 1.23L10 13V7h1z" />
              </svg>
              <span className="text-[7px] font-bold text-[#0c2340] tracking-tighter uppercase">सत्यमेव जयते</span>
            </div>

            <div>
              <div className="flex items-baseline gap-2">
                <h1 className="text-lg sm:text-xl font-bold text-[#0c2340] tracking-tight">राष्ट्रीय पोर्टल भारत</h1>
                <span className="text-sm font-semibold text-[#135c9e] hidden sm:inline">National Portal of India</span>
              </div>
              <p className="text-xs text-[#475569] font-medium">
                सेवा वाणी (Seva Vaani) &bull; National Public Welfare Multilingual Voice Assistant
              </p>
            </div>
          </div>

          {/* Status Indicators */}
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-300 text-emerald-800 font-medium flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-600" />
              {health?.engine || 'C++20 Core'}
            </span>

            <span className="px-2.5 py-1 rounded-md bg-blue-50 border border-blue-300 text-[#135c9e] font-medium flex items-center gap-1.5">
              <span className="material-symbols-outlined text-sm text-[#135c9e]">graphic_eq</span>
              Neural Audio Engine
            </span>

            {health && (
              <span
                className={`px-2.5 py-1 rounded-md font-medium border ${
                  health.groq_available
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-800'
                    : 'bg-amber-50 border-amber-300 text-amber-800'
                }`}
              >
                {health.groq_available ? 'Groq AI Active' : 'Offline Ready'}
              </span>
            )}
          </div>
        </div>
      </header>

      {/* 4. India.gov.in Official Navy Blue Navigation Ribbon */}
      <nav className="bg-[#135c9e] text-white px-4 sm:px-8 py-2 text-xs font-medium shadow-inner">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-4 sm:gap-6">
            <span className="hover:text-amber-200 cursor-pointer font-semibold flex items-center gap-1">
              <span className="material-symbols-outlined text-sm">home</span> मुख्य पृष्ठ (Home)
            </span>
            <span className="hover:text-amber-200 cursor-pointer">नागरिक सेवाएं (Services)</span>
            <span className="hover:text-amber-200 cursor-pointer">कृषि एवं किसान (Agriculture)</span>
            <span className="hover:text-amber-200 cursor-pointer">स्वास्थ्य (Health)</span>
            <span className="hover:text-amber-200 cursor-pointer">पेंशन (Pensions)</span>
          </div>

          <div className="flex items-center gap-2 text-amber-200 text-[11px]">
            <span className="material-symbols-outlined text-sm">phone_in_talk</span>
            <span>नागरिक हेल्पलाइन: 1800-11-2026 (Toll-Free)</span>
          </div>
        </div>
      </nav>

      {/* 5. Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 flex flex-col gap-5">
        {/* Error notification banner */}
        {errorMessage && (
          <div className="bg-amber-50 border-l-4 border-amber-600 p-3 text-amber-800 text-xs sm:text-sm rounded-r flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-amber-600 text-base">warning</span>
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-amber-900 font-bold hover:underline text-xs"
            >
              हटाएं (Dismiss)
            </button>
          </div>
        )}

        {/* Official Civic Voice Station Card */}
        <section className="bg-white border border-slate-200 rounded-xl shadow-md overflow-hidden">
          {/* Card Government Header Ribbon */}
          <div className="bg-[#0c2340] text-white px-5 py-3 border-b-2 border-[#FF9933] flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-amber-400 text-lg">record_voice_over</span>
              <h2 className="text-sm sm:text-base font-semibold tracking-wide">
                सेवा वाणी संवाद केंद्र | Seva Vaani Citizen Voice Terminal
              </h2>
            </div>

            {/* Terminal Actions */}
            <div className="flex items-center gap-2 text-xs">
              {/* Detected Language Pill */}
              <div className="bg-[#163155] border border-[#234574] px-2.5 py-1 rounded text-slate-200 flex items-center gap-1.5">
                <span className="text-slate-400">पहचानी गई भाषा:</span>
                <span className="font-bold text-amber-400">{LANGUAGE_REGISTRY[activeLanguage]?.name}</span>
              </div>

              {/* Auto-Listen Toggle */}
              <button
                onClick={() => setAutoListen(!autoListen)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded border transition-colors ${
                  autoListen
                    ? 'bg-blue-900/80 border-blue-500 text-blue-200'
                    : 'bg-slate-800 border-slate-700 text-slate-400'
                }`}
                title="Continuous dialogue after assistant responds"
              >
                <span className="material-symbols-outlined text-xs">sync</span>
                <span>{autoListen ? 'Auto-Listen: ON' : 'Auto-Listen: OFF'}</span>
              </button>

              {/* Mute / Unmute */}
              <button
                onClick={() => {
                  if (voiceOutputEnabled) JevVoiceEngine.stopSpeaking();
                  setVoiceOutputEnabled(!voiceOutputEnabled);
                }}
                className={`flex items-center gap-1 px-2.5 py-1 rounded border transition-colors ${
                  voiceOutputEnabled
                    ? 'bg-emerald-950 border-emerald-600 text-emerald-300'
                    : 'bg-slate-800 border-slate-700 text-slate-400'
                }`}
                title="Toggle voice output"
              >
                <span className="material-symbols-outlined text-xs">
                  {voiceOutputEnabled ? 'volume_up' : 'volume_off'}
                </span>
                <span>{voiceOutputEnabled ? 'Voice ON' : 'Muted'}</span>
              </button>

              {/* Clear */}
              <button
                onClick={clearChat}
                className="p-1 rounded text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                title="संवाद पुनः प्रारंभ करें (Clear)"
              >
                <span className="material-symbols-outlined text-base">refresh</span>
              </button>
            </div>
          </div>

          {/* Interactive Voice Stage */}
          <div className="p-6 sm:p-8 bg-gradient-to-b from-[#f8fafc] to-white flex flex-col items-center justify-center text-center">
            {/* Big Tactile Microphone Button */}
            <div className="relative mb-3">
              <button
                onClick={handleMicClick}
                disabled={voiceState === 'processing'}
                className={`w-28 h-28 sm:w-32 sm:h-32 rounded-full flex flex-col items-center justify-center transition-all duration-200 select-none shadow-xl relative z-10 ${
                  voiceState === 'listening'
                    ? 'bg-red-600 hover:bg-red-700 text-white ring-8 ring-red-300 animate-pulse scale-105'
                    : voiceState === 'speaking'
                    ? 'bg-[#135c9e] text-white ring-8 ring-blue-200'
                    : voiceState === 'processing'
                    ? 'bg-amber-600 text-white ring-8 ring-amber-200 cursor-wait'
                    : 'bg-[#0c2340] hover:bg-[#135c9e] text-white ring-4 ring-slate-300 hover:scale-105'
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
                <span className="text-[11px] font-bold mt-1 tracking-wider uppercase">
                  {voiceState === 'listening'
                    ? 'रोकें (Stop)'
                    : voiceState === 'processing'
                    ? 'सोच रहा है'
                    : voiceState === 'speaking'
                    ? 'बोल रहा है'
                    : 'बोलें (Speak)'}
                </span>
              </button>
            </div>

            {/* State Prompt */}
            <div className="w-full max-w-lg mt-2">
              <h3 className="text-base sm:text-lg font-bold text-[#0c2340]">
                {voiceState === 'listening' && 'आपकी आवाज़ सुनी जा रही है... किसी भी भाषा में बोलें'}
                {voiceState === 'processing' && 'समाधान तैयार किया जा रहा है... (Groq AI & C++ Core)'}
                {voiceState === 'speaking' && 'आवाज़ द्वारा उत्तर दिया जा रहा है...'}
                {voiceState === 'idle' && 'माइक बटन दबाएं और अपनी भाषा में बोलना शुरू करें'}
                {voiceState === 'error' && 'कोई त्रुटि हुई। कृपया पुनः प्रयास करें।'}
              </h3>

              {/* Real-time Dynamic Waveform */}
              <WaveformVisualizer state={voiceState} audioLevel={audioLevel} />

              {/* Interim Live Transcript */}
              {liveTranscript && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-2.5 text-xs sm:text-sm text-[#0c2340] italic font-medium mt-1">
                  "{liveTranscript}"
                </div>
              )}

              <p className="text-xs text-[#64748b] mt-1">
                स्वतः पहचानी जाने वाली भाषाएं: <strong>हिन्दी</strong> &bull; <strong>ગુજરાતી</strong> &bull;{' '}
                <strong>मराठी</strong> &bull; <strong>English</strong> (कोई भाषा चयन आवश्यक नहीं)
              </p>
            </div>
          </div>
        </section>

        {/* 6. Official Service Quick Starters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          <button
            onClick={() => handleSendMessage('नमस्ते जी, मुझे बताइए कि आप मेरे लिए क्या कर सकते हैं?')}
            className="p-3 bg-white hover:bg-slate-50 border border-slate-200 hover:border-[#135c9e] rounded-lg text-left transition-all shadow-sm flex flex-col justify-between"
          >
            <div className="flex items-center justify-between w-full mb-1">
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 uppercase">
                हिन्दी
              </span>
              <span className="material-symbols-outlined text-slate-400 text-sm">arrow_forward</span>
            </div>
            <span className="text-xs text-[#0c2340] font-semibold line-clamp-2">
              नमस्ते जी, आप मेरे लिए क्या कर सकते हैं?
            </span>
          </button>

          <button
            onClick={() => handleSendMessage('નમસ્તે, મને સરકારી સહાય અને ખેડૂત યોજનાઓ વિશે જણાવો.')}
            className="p-3 bg-white hover:bg-slate-50 border border-slate-200 hover:border-[#135c9e] rounded-lg text-left transition-all shadow-sm flex flex-col justify-between"
          >
            <div className="flex items-center justify-between w-full mb-1">
              <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 uppercase">
                ગુજરાતી
              </span>
              <span className="material-symbols-outlined text-slate-400 text-sm">arrow_forward</span>
            </div>
            <span className="text-xs text-[#0c2340] font-semibold line-clamp-2">
              સરકારી સહાય અને ખેડૂત યોજનાઓ વિશે જણાવો.
            </span>
          </button>

          <button
            onClick={() => handleSendMessage('नमस्कार, मला शासकीय योजना आणि नागरिक सेवांची माहिती द्या.')}
            className="p-3 bg-white hover:bg-slate-50 border border-slate-200 hover:border-[#135c9e] rounded-lg text-left transition-all shadow-sm flex flex-col justify-between"
          >
            <div className="flex items-center justify-between w-full mb-1">
              <span className="text-[10px] font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200 uppercase">
                मराठी
              </span>
              <span className="material-symbols-outlined text-slate-400 text-sm">arrow_forward</span>
            </div>
            <span className="text-xs text-[#0c2340] font-semibold line-clamp-2">
              शासकीय योजना आणि नागरिक सेवांची माहिती द्या.
            </span>
          </button>

          <button
            onClick={() => handleSendMessage('Hello, which public welfare schemes can I apply for?')}
            className="p-3 bg-white hover:bg-slate-50 border border-slate-200 hover:border-[#135c9e] rounded-lg text-left transition-all shadow-sm flex flex-col justify-between"
          >
            <div className="flex items-center justify-between w-full mb-1">
              <span className="text-[10px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200 uppercase">
                English
              </span>
              <span className="material-symbols-outlined text-slate-400 text-sm">arrow_forward</span>
            </div>
            <span className="text-xs text-[#0c2340] font-semibold line-clamp-2">
              Which public welfare schemes can I apply for?
            </span>
          </button>
        </div>

        {/* 7. Official Citizen Dialogue Feed */}
        <section className="bg-white border border-slate-200 rounded-xl shadow-md overflow-hidden flex flex-col min-h-[300px] max-h-[480px]">
          <div className="bg-[#f8fafc] border-b border-slate-200 px-4 py-2.5 flex items-center justify-between text-xs text-[#475569]">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#135c9e] text-base">forum</span>
              <span className="font-bold text-[#0c2340]">संवाद विवरण | Citizen Dialogue Record</span>
            </div>
            <span className="bg-slate-200 px-2 py-0.5 rounded font-mono text-[11px] text-slate-700">
              {messages.length} संदेश
            </span>
          </div>

          {/* Dialogue Message Thread */}
          <div ref={chatScrollRef} className="flex-1 p-4 overflow-y-auto space-y-4 custom-scroll bg-[#fafbfc]">
            {messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div key={msg.id} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                  {/* Meta Bar */}
                  <div className="flex items-center gap-1.5 mb-1 px-1 text-[11px] text-[#64748b]">
                    <span className="font-bold text-[#0c2340]">
                      {isUser ? 'नागरिक (Citizen)' : 'सेवा वाणी (Seva Vaani)'}
                    </span>
                    {msg.detectedLanguage && (
                      <span className="px-1.5 py-0.5 rounded bg-slate-100 border border-slate-300 text-[10px] text-[#135c9e] font-semibold">
                        {msg.languageName || msg.detectedLanguage}
                      </span>
                    )}
                    <span>&bull; {msg.timestamp}</span>
                  </div>

                  {/* Message Bubble */}
                  <div
                    className={`max-w-[85%] rounded-lg p-3.5 text-sm leading-relaxed ${
                      isUser
                        ? 'bg-[#135c9e] text-white rounded-tr-none shadow-sm'
                        : 'bg-white text-[#1e293b] rounded-tl-none border border-slate-200 shadow-sm'
                    }`}
                  >
                    <p className="whitespace-pre-wrap font-normal">{msg.content}</p>

                    {/* Assistant Action Bar */}
                    {!isUser && (
                      <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-[#64748b]">
                        <span className="text-[10px] text-slate-500 font-mono">
                          {msg.model || 'Groq Core AI'}
                        </span>

                        <div className="flex items-center gap-3">
                          {/* Neural Voice Playback Button */}
                          <button
                            onClick={() => vocalize(msg.content, msg.detectedLanguage || 'hi')}
                            className="flex items-center gap-1 text-[#135c9e] hover:text-[#0c2340] font-semibold transition-colors"
                            title="बोलकर सुनें (Play Neural Voice)"
                          >
                            <span className="material-symbols-outlined text-sm">volume_up</span>
                            <span>बोलकर सुनें</span>
                          </button>

                          <button
                            onClick={() => navigator.clipboard.writeText(msg.content)}
                            className="flex items-center gap-1 text-slate-500 hover:text-slate-800 transition-colors"
                            title="कॉपी करें"
                          >
                            <span className="material-symbols-outlined text-sm">content_copy</span>
                            <span>कॉपी</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* 8. Text Input Fallback Bar */}
          <div className="p-3 border-t border-slate-200 bg-white flex items-center gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSendMessage(inputText);
              }}
              placeholder="यहाँ प्रश्न लिखें (हिन्दी, ગુજરાતી, मराठी या English में)..."
              className="flex-1 bg-[#f8fafc] border border-slate-300 rounded-lg px-3.5 py-2 text-sm text-[#0c2340] placeholder-slate-400 focus:outline-none focus:border-[#135c9e] focus:bg-white transition-colors"
            />
            <button
              onClick={() => handleSendMessage(inputText)}
              disabled={!inputText.trim() || voiceState === 'processing'}
              className="px-4 py-2 rounded-lg bg-[#135c9e] hover:bg-[#0c2340] disabled:opacity-50 text-white text-sm font-semibold transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-sm">send</span>
              <span className="hidden sm:inline">भेजें (Send)</span>
            </button>
          </div>
        </section>
      </main>

      {/* 9. Official India.gov.in 4-Column Footer */}
      <footer className="bg-[#0c2340] text-[#cbd5e1] border-t-2 border-[#138808] mt-8 text-xs">
        <div className="max-w-6xl mx-auto px-4 sm:px-8 py-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <h4 className="text-white font-bold text-sm mb-2.5">राष्ट्रीय पोर्टल भारत</h4>
            <p className="text-slate-400 text-xs leading-relaxed mb-2">
              National Portal of India provides a single-window access to information and services being provided by the
              various Indian Government entities.
            </p>
            <span className="text-[11px] text-amber-300">National Informatics Centre (NIC)</span>
          </div>

          <div>
            <h4 className="text-white font-bold text-sm mb-2.5">प्रमुख सरकारी पोर्टल</h4>
            <ul className="space-y-1 text-xs text-slate-300">
              <li className="hover:text-white cursor-pointer">&bull; MyGov नागरिक मंच</li>
              <li className="hover:text-white cursor-pointer">&bull; डिजिटल इंडिया पहल</li>
              <li className="hover:text-white cursor-pointer">&bull; डिजीलॉकर नागरिक दस्तावेज़</li>
              <li className="hover:text-white cursor-pointer">&bull; भारतीय विशिष्ट पहचान प्राधिकरण (UIDAI)</li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-bold text-sm mb-2.5">नागरिक सहायता एवं नीतियां</h4>
            <ul className="space-y-1 text-xs text-slate-300">
              <li className="hover:text-white cursor-pointer">&bull; गोपनीयता नीति (Privacy Policy)</li>
              <li className="hover:text-white cursor-pointer">&bull; हाइपरलिंकिंग नीति</li>
              <li className="hover:text-white cursor-pointer">&bull; कॉपीराइट नीति एवं नियम</li>
              <li className="hover:text-white cursor-pointer">&bull; सुलभता वक्तव्य (Accessibility)</li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-bold text-sm mb-2.5">सहायता केंद्र</h4>
            <p className="text-slate-400 text-xs mb-2">
              तकनीकी सहायता या सेवा वाणी से संबंधित सुझाव के लिए संपर्क करें:
            </p>
            <p className="text-white font-mono font-semibold">helpdesk-india@gov.in</p>
            <p className="text-amber-300 text-xs font-semibold mt-1">टोल-फ्री: 1800-11-2026</p>
          </div>
        </div>

        <div className="border-t border-[#163155] py-3 text-center text-[11px] text-slate-400 bg-[#08182b]">
          पोर्टल सामग्री प्रबंधन: भारत सरकार &bull; अभिकल्पना एवं विकास: राष्ट्रीय सूचना विज्ञान केंद्र (NIC)
        </div>
      </footer>
    </div>
  );
};

export default App;
