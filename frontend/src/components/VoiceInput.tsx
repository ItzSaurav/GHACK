import React, { useState, useEffect } from 'react';
import { Language } from '../types';

interface VoiceInputProps {
  language: Language;
  isListening: boolean;
  audioLevel?: number;
  isUserSpeaking?: boolean;
  transcript: string;
  onTranscriptChange: (text: string) => void;
  confidence: number | null;
  speechError: string | null;
  onStartListening: () => void;
  onStopListening: () => void;
  onSendMessage: (text: string, source: 'voice' | 'text', confidence?: number) => void;
  onUploadAudioFile: (file: File | Blob) => void;
  disabled: boolean;
  suggestions?: string[];
  onSelectSuggestion?: (text: string) => void;
}

export const VoiceInput: React.FC<VoiceInputProps> = ({
  language,
  isListening,
  audioLevel = 0,
  isUserSpeaking = false,
  transcript,
  onTranscriptChange,
  confidence,
  speechError,
  onStartListening,
  onStopListening,
  onSendMessage,
  onUploadAudioFile,
  disabled,
  suggestions = [],
  onSelectSuggestion,
}) => {
  const [manualText, setManualText] = useState('');
  const [showUploader, setShowUploader] = useState(false);

  const handleMicClick = () => {
    if (disabled) return;
    if (isListening) {
      onStopListening();
    } else {
      onStartListening();
    }
  };

  // Keyboard shortcut Alt + V to toggle microphone
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === 'v' || e.key === 'V')) {
        e.preventDefault();
        handleMicClick();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isListening, disabled]);

  const handleSendTranscript = () => {
    if (transcript.trim()) {
      onSendMessage(transcript.trim(), 'voice', confidence ?? 0.85);
      onTranscriptChange('');
    }
  };

  const handleSendManual = (e: React.FormEvent) => {
    e.preventDefault();
    if (manualText.trim()) {
      onSendMessage(manualText.trim(), 'text');
      setManualText('');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUploadAudioFile(e.target.files[0]);
      setShowUploader(false);
    }
  };

  return (
    <div className="voice-input-container">
      {/* Quick Suggestions Chips Strip */}
      {suggestions.length > 0 && (
        <div className="suggestion-chips-bar" aria-label="Spoken suggestions">
          <span className="suggestion-label">
            <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>touch_app</span>
            {language === 'hi' ? 'सुझाव:' : 'Suggestions:'}
          </span>
          {suggestions.map((sug, idx) => (
            <button
              key={idx}
              type="button"
              className="suggestion-chip"
              onClick={() => {
                if (onSelectSuggestion) {
                  onSelectSuggestion(sug);
                } else {
                  onSendMessage(sug, 'text');
                }
              }}
              disabled={disabled}
            >
              {sug}
            </button>
          ))}
        </div>
      )}

      {/* Civic Voice Clarity Visualizer Action Dock */}
      <div className="voice-visualizer-dock">
        {/* 7-Bar Audio Waveform Visualizer & Status */}
        <div className="waveform-meta-group">
          <div className="waveform-capsule" aria-hidden="true">
            <span className={`wave-bar ${isListening ? 'wave-bar-1' : ''}`} style={{ height: isListening ? (isUserSpeaking ? `${Math.max(6, Math.round(audioLevel * 32 * 0.7))}px` : undefined) : '8px' }}></span>
            <span className={`wave-bar ${isListening ? 'wave-bar-2' : ''}`} style={{ height: isListening ? (isUserSpeaking ? `${Math.max(8, Math.round(audioLevel * 32 * 1.1))}px` : undefined) : '16px' }}></span>
            <span className={`wave-bar ${isListening ? 'wave-bar-3' : ''}`} style={{ height: isListening ? (isUserSpeaking ? `${Math.max(10, Math.round(audioLevel * 32 * 1.3))}px` : undefined) : '22px' }}></span>
            <span className={`wave-bar ${isListening ? 'wave-bar-4' : ''}`} style={{ height: isListening ? (isUserSpeaking ? `${Math.max(12, Math.round(audioLevel * 32 * 1.0))}px` : undefined) : '14px' }}></span>
            <span className={`wave-bar ${isListening ? 'wave-bar-5' : ''}`} style={{ height: isListening ? (isUserSpeaking ? `${Math.max(10, Math.round(audioLevel * 32 * 1.2))}px` : undefined) : '18px' }}></span>
            <span className={`wave-bar ${isListening ? 'wave-bar-6' : ''}`} style={{ height: isListening ? (isUserSpeaking ? `${Math.max(8, Math.round(audioLevel * 32 * 0.9))}px` : undefined) : '10px' }}></span>
            <span className={`wave-bar ${isListening ? 'wave-bar-7' : ''}`} style={{ height: isListening ? (isUserSpeaking ? `${Math.max(6, Math.round(audioLevel * 32 * 0.8))}px` : undefined) : '15px' }}></span>
          </div>

          <div className="waveform-label-col">
            <span className="waveform-status-text" aria-live="polite">
              {isListening
                ? (isUserSpeaking
                    ? (language === 'hi' ? 'आवाज़ पहचानी जा रही है...' : (language === 'kn' ? 'ಮಾತು ಗುರುತಿಸಲಾಗುತ್ತಿದೆ...' : 'Speech detected... listening'))
                    : (language === 'hi' ? 'सुन रहा हूँ... बोलिए' : (language === 'kn' ? 'ಕೇಳಿಸಿಕೊಳ್ಳುತ್ತಿದ್ದೇನೆ...' : 'Listening... speak clearly')))
                : (language === 'hi' ? 'आवाज़ सहायक तैयार है' : 'Voice assistant ready')}
            </span>
            <span className="waveform-sub-text">
              {isListening
                ? (isUserSpeaking
                    ? (language === 'hi' ? 'बोलना समाप्त होने पर स्वतः भेजेगा' : 'Auto-stops when you pause')
                    : (language === 'hi' ? 'भारतीय भाषा पहचान सक्रिय' : 'Voice activity detection active'))
                : (language === 'hi' ? 'बोलने के लिए माइक दबाएं' : 'Tap mic to speak')}
            </span>
          </div>
        </div>

        {/* Pulsing Primary Microphone Button with Concentric Ripple */}
        <div className="mic-btn-wrapper">
          {isListening && <div className="mic-pulse-ripple voice-pulse-ring" aria-hidden="true"></div>}
          <button
            type="button"
            className={`mic-button-civic ${isListening ? 'is-listening' : ''}`}
            onClick={handleMicClick}
            disabled={disabled}
            aria-label={
              isListening
                ? (language === 'hi' ? 'रिकॉर्डिंग रोकें (Alt + V)' : 'Stop recording (Alt + V)')
                : (language === 'hi' ? 'बोलने के लिए माइक दबाएं (Alt + V)' : 'Tap to speak (Alt + V)')
            }
            title={isListening ? 'Stop recording (Alt + V)' : 'Tap to speak (Alt + V)'}
          >
            <span
              className="material-symbols-outlined"
              style={{ fontSize: '28px', fontVariationSettings: "'FILL' 1" }}
            >
              mic
            </span>
          </button>
        </div>

        {/* Keyboard Shortcut Hint (Desktop) */}
        <div className="shortcut-hint" title="Press Alt + V to toggle microphone anywhere">
          <kbd className="shortcut-key">Alt + V</kbd>
          <span>{language === 'hi' ? 'माइक' : 'to mic'}</span>
        </div>
      </div>

      {/* Speech Error Banner */}
      {speechError && (
        <div className="alert-banner alert-warning" role="alert">
          <p>{speechError}</p>
        </div>
      )}

      {/* Recognized Transcript & Correction Card */}
      {(transcript || isListening) && (
        <div className="transcript-box">
          <div className="transcript-header">
            <span className="transcript-title">
              {language === 'hi' ? 'सुनी गई बात (समीक्षा व सुधार करें):' : 'Heard transcript (Review and correct):'}
            </span>
            {confidence !== null && (
              <span className="confidence-pill">
                {language === 'hi' ? 'सटीकता:' : 'Confidence:'} {Math.round(confidence * 100)}%
              </span>
            )}
          </div>

          <textarea
            className="transcript-textarea"
            value={transcript}
            onChange={(e) => onTranscriptChange(e.target.value)}
            placeholder={
              language === 'hi'
                ? 'यदि आवाज सही नहीं सुनी गई, तो यहाँ सुधार कर सकते हैं...'
                : 'If recognized text needs correction, edit here before sending...'
            }
            rows={2}
          />

          <div className="transcript-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleSendTranscript}
              disabled={!transcript.trim() || disabled}
            >
              {language === 'hi' ? 'पुष्टि करें और भेजें' : 'Confirm & Send'}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => onTranscriptChange('')}
              disabled={disabled}
            >
              {language === 'hi' ? 'रद्द करें' : 'Clear'}
            </button>
          </div>
        </div>
      )}

      {/* Text Input Fallback */}
      <form className="text-fallback-form" onSubmit={handleSendManual}>
        <input
          type="text"
          className="text-fallback-input"
          value={manualText}
          onChange={(e) => setManualText(e.target.value)}
          placeholder={
            language === 'hi'
              ? 'अथवा यहाँ लिखकर उत्तर दें (उदा. किसान, 2 एकड़, 1.8 लाख)...'
              : 'Or type your answer here (e.g., farmer, 2 acres, 1.8 Lakhs)...'
          }
          disabled={disabled}
        />
        <button
          type="submit"
          className="btn btn-submit"
          disabled={!manualText.trim() || disabled}
          aria-label="Send message"
        >
          {language === 'hi' ? 'भेजें' : 'Send'}
        </button>
      </form>

      {/* Audio File Upload & Privacy Disclaimer */}
      <div className="privacy-shield-bar">
        <span className="material-symbols-outlined shield-icon" aria-hidden="true">
          shield
        </span>
        <span>
          {language === 'hi'
            ? 'आवाज़ डेटा केवल योजना मिलान के लिए स्थानीय रूप से संसाधित होता है, आधार से लिंक नहीं होता।'
            : 'Voice data is processed locally for scheme filtering and not stored or linked to Aadhaar.'}
        </span>
      </div>

      <div className="upload-fallback-toggle">
        <button
          type="button"
          className="link-btn"
          onClick={() => setShowUploader(!showUploader)}
        >
          {language === 'hi' ? 'ऑडियो फ़ाइल अपलोड करें' : 'Upload recorded audio file'}
        </button>
        {showUploader && (
          <div className="file-uploader-box">
            <label htmlFor="audio-file-input">
              {language === 'hi' ? 'ऑडियो फ़ाइल चुनें (अधिकतम 5MB):' : 'Select audio file (Max 5MB):'}
            </label>
            <input
              id="audio-file-input"
              type="file"
              accept="audio/*,.wav,.webm,.mp3"
              onChange={handleFileChange}
            />
          </div>
        )}
      </div>
    </div>
  );
};

