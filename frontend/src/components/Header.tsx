import React from 'react';
import { Language } from '../types';

interface HeaderProps {
  language: Language;
  onLanguageChange: (lang: Language) => void;
  speechEnabled: boolean;
  onToggleSpeech: () => void;
  onRestart: () => void;
  isOnline: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  language,
  onLanguageChange,
  speechEnabled,
  onToggleSpeech,
  onRestart,
  isOnline,
}) => {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-emblem" aria-hidden="true">
          <div className="emblem-inner">GOV</div>
        </div>
        <div className="brand-titles">
          <h1 className="main-title">
            {language === 'hi' ? 'जन कल्याण योजना सहायक' : 'Citizen Scheme Assistant'}
          </h1>
          <p className="sub-title">
            {language === 'hi'
              ? 'आवाज से सरकारी योजनाओं की खोज एवं फॉर्म सहायता'
              : 'Voice-First Government Welfare Discovery & Form Guidance'}
          </p>
        </div>
      </div>

      <div className="header-controls">
        {/* Offline indicator */}
        {!isOnline && (
          <span className="badge badge-offline" role="status">
            {language === 'hi' ? 'ऑफ़लाइन (Offline)' : 'Offline Mode'}
          </span>
        )}

        {/* Voice Read-Aloud Toggle */}
        <button
          type="button"
          className={`control-btn ${speechEnabled ? 'control-btn-active' : ''}`}
          onClick={onToggleSpeech}
          title={language === 'hi' ? 'सहायक की आवाज चालू/बंद करें' : 'Toggle Voice Output'}
          aria-label={speechEnabled ? 'Mute assistant voice' : 'Enable assistant voice'}
        >
          {speechEnabled
            ? (language === 'hi' ? 'आवाज: चालू' : 'Voice: ON')
            : (language === 'hi' ? 'आवाज: बंद' : 'Voice: OFF')}
        </button>

        {/* Language Selector */}
        <div className="language-toggle" role="group" aria-label="Language Selector">
          <button
            type="button"
            className={`lang-btn ${language === 'hi' ? 'active' : ''}`}
            onClick={() => onLanguageChange('hi')}
          >
            हिंदी
          </button>
          <button
            type="button"
            className={`lang-btn ${language === 'en' ? 'active' : ''}`}
            onClick={() => onLanguageChange('en')}
          >
            English
          </button>
        </div>

        {/* Restart Button */}
        <button
          type="button"
          className="restart-btn"
          onClick={onRestart}
          title={language === 'hi' ? 'बातचीत शुरू से प्रारंभ करें' : 'Start over conversation'}
        >
          {language === 'hi' ? 'नया सत्र' : 'Restart'}
        </button>
      </div>
    </header>
  );
};
