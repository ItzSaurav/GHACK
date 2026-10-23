import { useState, useEffect, useRef, useCallback } from 'react';
import { Language } from '../types';

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
    AudioContext: any;
    webkitAudioContext: any;
  }
}

export const LANG_CODE_MAP: Record<Language, string> = {
  en: 'en-IN',
  kn: 'kn-IN',
  hi: 'hi-IN',
  gu: 'gu-IN',
  ta: 'ta-IN',
  te: 'te-IN',
  ur: 'ur-IN',
  or: 'or-IN',
  mr: 'mr-IN',
  ml: 'ml-IN',
};

interface UseSpeechOptions {
  onAudioCaptured?: (blob: Blob) => void;
  onSpeechEnded?: () => void;
}

export function useSpeech(currentLanguage: Language, options?: UseSpeechOptions) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [confidence, setConfidence] = useState<number | null>(null);
  const [speechError, setSpeechError] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechEnabled, setSpeechEnabled] = useState(true);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);

  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // VAD & Silence Detection Refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const vadIntervalRef = useRef<any>(null);
  const hasSpokenRef = useRef(false);
  const silenceStartRef = useRef<number | null>(null);
  const listenStartRef = useRef<number>(0);

  const cleanupAudioPipeline = () => {
    if (vadIntervalRef.current) {
      clearInterval(vadIntervalRef.current);
      vadIntervalRef.current = null;
    }
    if (audioContextRef.current) {
      try {
        if (audioContextRef.current.state !== 'closed') {
          audioContextRef.current.close();
        }
      } catch {
        // Ignore
      }
      audioContextRef.current = null;
    }
    setAudioLevel(0);
    setIsUserSpeaking(false);
    hasSpokenRef.current = false;
    silenceStartRef.current = null;
  };

  const stopListening = useCallback(() => {
    cleanupAudioPipeline();

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore
      }
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      try {
        mediaRecorderRef.current.stop();
      } catch {
        // Ignore
      }
    }
    setIsListening(false);
  }, []);

  // Initialize Speech Recognition if supported in the browser
  useEffect(() => {
    const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognitionClass) {
      try {
        const recognition = new SpeechRecognitionClass();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = LANG_CODE_MAP[currentLanguage] || 'hi-IN';

        recognition.onresult = (event: any) => {
          let interim = '';
          let final = '';
          let conf = 0.85;

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const item = event.results[i];
            if (item.isFinal) {
              final += item[0].transcript;
              if (item[0].confidence) {
                conf = item[0].confidence;
              }
            } else {
              interim += item[0].transcript;
            }
          }

          const recognized = final || interim;
          if (recognized) {
            setTranscript(recognized);
            setConfidence(conf);
            hasSpokenRef.current = true;
          }
        };

        recognition.onerror = (_event: any) => {
          // Native browser recognition error (e.g. 'network' on Linux Chromium)
          // Gracefully handled as backend MediaRecorder handles robust ASR
        };

        recognition.onend = () => {
          // End of recognition stream
        };

        recognitionRef.current = recognition;
      } catch {
        recognitionRef.current = null;
      }
    }
  }, [currentLanguage]);

  const startListening = useCallback(async () => {
    setSpeechError(null);
    setTranscript('');
    setConfidence(null);
    audioChunksRef.current = [];
    cleanupAudioPipeline();

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setSpeechError('Microphone access is not supported in this browser. Please type your reply below.');
      return;
    }

    try {
      // Request microphone with hardware-level noise suppression and acoustic echo cancellation
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
        },
      });
      streamRef.current = stream;

      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : MediaRecorder.isTypeSupported('audio/ogg')
        ? 'audio/ogg'
        : 'audio/wav';

      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        cleanupAudioPipeline();
        const recordedBlob = new Blob(audioChunksRef.current, {
          type: mimeType || 'audio/webm',
        });
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
        setIsListening(false);
        if (options?.onAudioCaptured && recordedBlob.size > 0) {
          options.onAudioCaptured(recordedBlob);
        }
      };

      // Voice Activity Detection (VAD) via Web Audio API AnalyserNode
      const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
      if (AudioCtxClass) {
        try {
          const audioCtx = new AudioCtxClass();
          audioContextRef.current = audioCtx;
          const sourceNode = audioCtx.createMediaStreamSource(stream);
          const analyser = audioCtx.createAnalyser();
          analyser.fftSize = 256;
          analyser.smoothingTimeConstant = 0.35;
          sourceNode.connect(analyser);

          listenStartRef.current = Date.now();
          hasSpokenRef.current = false;
          silenceStartRef.current = null;

          const buffer = new Uint8Array(analyser.fftSize);

          vadIntervalRef.current = setInterval(() => {
            analyser.getByteTimeDomainData(buffer);
            let sumSq = 0;
            for (let i = 0; i < buffer.length; i++) {
              const norm = (buffer[i] - 128) / 128;
              sumSq += norm * norm;
            }
            const rms = Math.sqrt(sumSq / buffer.length);
            setAudioLevel(Math.min(1, rms * 4.5));

            // Thresholds calibrated for microphone speech vs ambient background noise
            const SPEECH_RMS_THRESHOLD = 0.038;
            const SILENCE_RMS_THRESHOLD = 0.024;

            if (rms >= SPEECH_RMS_THRESHOLD) {
              // Active voice detected
              hasSpokenRef.current = true;
              silenceStartRef.current = null;
              setIsUserSpeaking(true);
            } else if (rms <= SILENCE_RMS_THRESHOLD) {
              setIsUserSpeaking(false);
              const now = Date.now();

              if (hasSpokenRef.current) {
                // Citizen was speaking and has now paused/concluded
                if (silenceStartRef.current === null) {
                  silenceStartRef.current = now;
                } else if (now - silenceStartRef.current >= 1350) {
                  // Concluded turn: 1.35s continuous silence after speech
                  stopListening();
                }
              } else {
                // No speech has occurred yet; timeout after 7.5s of empty room silence
                if (now - listenStartRef.current >= 7500) {
                  stopListening();
                }
              }
            }
          }, 65);
        } catch {
          // If AudioContext creation fails, fallback to manual stop
        }
      }

      mediaRecorder.start(250);
      setIsListening(true);

      // Start native recognition in parallel for real-time visual feedback if available
      if (recognitionRef.current) {
        try {
          recognitionRef.current.lang = LANG_CODE_MAP[currentLanguage] || 'hi-IN';
          recognitionRef.current.start();
        } catch {
          // Ignore parallel start errors
        }
      }
    } catch (err: any) {
      setIsListening(false);
      cleanupAudioPipeline();
      setSpeechError('Microphone access denied. Please allow microphone permissions or type your reply below.');
    }
  }, [currentLanguage, options, stopListening]);

  const stopSpeaking = useCallback(() => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.currentTime = 0;
      audioPlayerRef.current = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  }, []);

  // Text-to-Speech using backend neural Edge TTS with browser SpeechSynthesis fallback
  const speak = useCallback(
    (text: string, lang: Language) => {
      if (!speechEnabled || !text.trim()) return;

      stopSpeaking();
      setIsSpeaking(true);

      const encoded = encodeURIComponent(text.trim());
      const audioUrl = `/api/v1/voice/tts?text=${encoded}&language=${lang}`;
      const audio = new Audio(audioUrl);
      audioPlayerRef.current = audio;

      audio.onended = () => {
        setIsSpeaking(false);
        audioPlayerRef.current = null;
        if (options?.onSpeechEnded) {
          options.onSpeechEnded();
        }
      };

      const fallbackToWebSpeech = () => {
        if (window.speechSynthesis) {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.lang = LANG_CODE_MAP[lang] || 'hi-IN';
          utterance.rate = 0.95;
          utterance.onend = () => {
            setIsSpeaking(false);
            if (options?.onSpeechEnded) {
              options.onSpeechEnded();
            }
          };
          utterance.onerror = () => setIsSpeaking(false);
          window.speechSynthesis.speak(utterance);
        } else {
          setIsSpeaking(false);
        }
      };

      audio.onerror = () => {
        fallbackToWebSpeech();
      };

      audio.play().catch((_err) => {
        // Autoplay policy or media decode error fallback
        fallbackToWebSpeech();
      });
    },
    [speechEnabled, stopSpeaking, options]
  );

  return {
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
    hasNativeSpeechRecognition: Boolean(window.SpeechRecognition || window.webkitSpeechRecognition),
  };
}
