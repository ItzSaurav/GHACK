import React from 'react';
import { Language } from '../types';

interface QuestionCardProps {
  language: Language;
  questionText: string;
  options: string[];
  onSelectOption: (option: string) => void;
  onSpeakAgain: () => void;
  isSpeaking: boolean;
  disabled: boolean;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  language,
  questionText,
  options,
  onSelectOption,
  onSpeakAgain,
  isSpeaking,
  disabled,
}) => {
  return (
    <div className="question-card" role="region" aria-label="Current Question">
      <div className="question-header">
        <span className="badge badge-assistant">
          {language === 'hi' ? 'सहायक का प्रश्न' : "Assistant's Question"}
        </span>

        {/* Read-Aloud Button */}
        <button
          type="button"
          className={`speak-again-btn ${isSpeaking ? 'speaking-active' : ''}`}
          onClick={onSpeakAgain}
          title={language === 'hi' ? 'प्रश्न दोबारा सुनें' : 'Listen to question again'}
          aria-label={language === 'hi' ? 'प्रश्न आवाज में सुनें' : 'Read question aloud'}
        >
          {isSpeaking
            ? (language === 'hi' ? 'बोल रहा है...' : 'Speaking...')
            : (language === 'hi' ? 'बोलकर सुनाएं' : 'Listen')}
        </button>
      </div>

      <div className="question-body">
        <p className="question-text">{questionText}</p>
      </div>

      {/* Quick Select Options Chips */}
      {options && options.length > 0 && (
        <div className="options-container">
          <p className="options-hint">
            {language === 'hi' ? 'या नीचे दिए गए विकल्पों में से चुनें:' : 'Or tap an option below:'}
          </p>
          <div className="options-grid">
            {options.map((opt, index) => (
              <button
                key={index}
                type="button"
                className="option-chip"
                onClick={() => onSelectOption(opt)}
                disabled={disabled}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
