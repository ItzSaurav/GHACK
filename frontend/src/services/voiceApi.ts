import { ChatResponse, ServerHealth, VoiceInteractResponse } from '../types';

const API_BASE = '/api';

export const voiceApi = {
  async getHealth(): Promise<ServerHealth> {
    const res = await fetch(`${API_BASE}/health`, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Health check failed with status ${res.status}`);
    }
    return res.json();
  },

  async sendChatMessage(
    message: string,
    history: { role: string; content: string }[] = [],
    language: string = 'auto'
  ): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        message,
        history,
        language,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Chat failed with HTTP ${res.status}`);
    }
    return res.json();
  },

  async interactWithAudio(
    audioBlob: Blob,
    history: { role: string; content: string }[] = [],
    filename: string = 'utterance.webm'
  ): Promise<VoiceInteractResponse> {
    const formData = new FormData();
    formData.append('audio', audioBlob, filename);
    formData.append('history', JSON.stringify(history));

    const res = await fetch(`${API_BASE}/voice/interact`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Voice interaction failed with HTTP ${res.status}`);
    }
    return res.json();
  },

  async transcribeAudio(
    audioBlob: Blob,
    filename: string = 'utterance.webm'
  ): Promise<{ text: string; detected_language: string; language_name: string; bcp47: string }> {
    const formData = new FormData();
    formData.append('file', audioBlob, filename);

    const res = await fetch(`${API_BASE}/transcribe`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Audio transcription failed with HTTP ${res.status}`);
    }
    return res.json();
  },
};
