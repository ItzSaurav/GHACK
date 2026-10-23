import { FormPreview, FormSubmissionReceipt, Language } from '../types';

const API_BASE = '/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
        ...(options.headers || {}),
      },
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.detail || `Request failed with status ${res.status}`;
      throw new Error(msg);
    }

    return await res.json();
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error('Network timeout: Server took too long to respond. Please check your connection.');
    }
    throw err;
  }
}

export const api = {
  checkHealth: () => request<any>('/health'),

  listSchemes: () => request<any[]>('/schemes'),

  getScheme: (schemeId: string) => request<any>(`/schemes/${schemeId}`),

  startConversation: (language: Language) =>
    request<{
      session_id: string;
      language: Language;
      greeting: string;
      current_question_key: string;
      options: string[];
    }>('/conversation/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language }),
    }),

  sendMessage: (sessionId: string, text: string, source: 'text' | 'voice' = 'text', audioConfidence?: number) =>
    request<{
      session_id: string;
      reply: string;
      current_question_key: string | null;
      options: string[];
      facts: Record<string, any>;
      evaluation: any[];
      is_completed: boolean;
      detected_language?: Language;
      open_form_scheme_id?: string | null;
    }>('/conversation/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        text,
        source,
        audio_confidence: audioConfidence ?? null,
      }),
    }),

  uploadVoice: (sessionId: string, language: Language, audioBlob: Blob) => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('language', language);
    formData.append('audio', audioBlob, 'utterance.wav');

    return request<{
      success: boolean;
      transcription: any;
      dialogue_response: any;
      message?: string;
    }>('/conversation/voice', {
      method: 'POST',
      body: formData,
    });
  },

  getFormPreview: (sessionId: string, schemeId: string) =>
    request<FormPreview>('/forms/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, scheme_id: schemeId }),
    }),

  submitForm: (
    formId: string,
    schemeId: string,
    citizenApproval: boolean,
    reviewedFields: Record<string, any>,
    language: Language
  ) =>
    request<FormSubmissionReceipt>('/forms/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        form_id: formId,
        scheme_id: schemeId,
        citizen_explicit_approval: citizenApproval,
        reviewed_fields: reviewedFields,
        language,
      }),
    }),
};
