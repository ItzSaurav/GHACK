export type LanguageCode = 'en' | 'hi' | 'gu' | 'mr';

export interface LanguageInfo {
  code: LanguageCode;
  name: string;
  bcp47: string;
}

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

export interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  detectedLanguage?: LanguageCode;
  languageName?: string;
  bcp47?: string;
  model?: string;
  timestamp: string;
}

export interface ServerHealth {
  status: string;
  engine: string;
  groq_available: boolean;
  languages: LanguageInfo[];
}

export interface ChatResponse {
  success: boolean;
  reply: string;
  detected_language: LanguageCode;
  language_name: string;
  bcp47: string;
  model: string;
  error?: string;
}

export interface VoiceInteractResponse {
  success: boolean;
  transcription: string;
  reply: string;
  detected_language: LanguageCode;
  language_name: string;
  bcp47: string;
  model: string;
  error?: string;
}
