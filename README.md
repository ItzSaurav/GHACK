# Sahaay Voice — Multilingual Conversational AI Assistant

A high-performance conversational voice assistant powered by a modern C++20 backend and a clean, responsive React frontend. Built for zero-friction multilingual voice interactions across 4 Indian languages with automatic language detection, conversational reasoning via Groq Cloud, and speech playback.

---

## 1. System Architecture

```
+-------------------------------------------------------------------------------+
|                       REACT CONVERSATIONAL WEB APP (VITE)                     |
|  - Real-Time Voice Interaction with Live Waveform Visualizer                  |
|  - Zero Manual Language Selectors (100% Automated Spoken Detection)           |
|  - Instant Browser TTS Vocalization (en-IN, hi-IN, gu-IN, mr-IN)             |
|  - Jev Voice Intelligence (Client-Side Script & Confidence Analyzer)           |
|  - Auto-Listen Mode for Hands-Free Continuous Dialogue                        |
+-------------------------------------------------------------------------------+
                                        |
                 HTTP REST / Multipart Audio (via /api/* proxy)
                                        v
+-------------------------------------------------------------------------------+
|                        C++20 BACKEND SERVICE (PORT 8000)                      |
|  - High-Throughput HTTP Server (cpp-httplib, C++20 Standard)                  |
|  - libcurl + OpenSSL for Secure HTTPS Client Requests to Groq API             |
|  - nlohmann/json for Robust Schema Serialization and Validation               |
|  - Multilingual Language Detector for English, Hindi, Gujarati, Marathi       |
|  - Deterministic Offline Fallback Engine (Active when API Key is absent)      |
+-------------------------------------------------------------------------------+
                                        |
                            Secure HTTPS API Requests
                                        v
+-------------------------------------------------------------------------------+
|                               GROQ CLOUD API                                  |
|  - Whisper Large v3 (Acoustic Audio Transcription & Native Language ID)       |
|  - LLaMA 3.3 70B Versatile (Voice-Optimized Conversational Reasoning)          |
+-------------------------------------------------------------------------------+
```

---

## 2. 4 Auto-Detected Languages

The application features zero manual language dropdowns or toggles. A citizen simply speaks, and the system identifies and converses in the matching language:

1. **English (`en`)**: Pan-Indian communicative voice (`en-IN`).
2. **Hindi (`hi`)**: Devanagari script (`\u0900-\u097F`) with Hindi morpho-syntactic markers (`hi-IN`).
3. **Gujarati (`gu`)**: Gujarati script (`\u0A80-\u0AFF`) with Gujarati morpho-syntactic markers (`gu-IN`).
4. **Marathi (`mr`)**: Devanagari script with Marathi lexical markers and morphological patterns (`mr-IN`).

---

## 3. Endpoints

| Endpoint | Method | Payload | Description |
|---|---|---|---|
| `/api/health` | GET | None | Server health status, C++ core status, Groq availability, supported languages |
| `/api/chat` | POST | JSON (`{ "message": "...", "history": [...] }`) | Multilingual conversational response with auto-detected language metadata |
| `/api/transcribe` | POST | Multipart audio (`file`) | Audio transcription using Groq Whisper with automatic language detection |
| `/api/voice/interact` | POST | Multipart audio (`audio`, optional `history`) | End-to-end voice processing: transcribes audio and generates conversational answer |

---

## 4. Setup and Execution

### Prerequisites
- Modern C++ compiler with C++20 support (`g++` 12+ or `clang++` 15+)
- `cmake` (3.20+) and `make`
- `libcurl` and `openssl` विकास libraries (`libcurl-dev`, `libssl-dev` or Arch equivalents)
- Node.js (18+) and npm

### Environment Variables
Configure your Groq API key in `.env`:
```bash
GROQ_API_KEY=your_groq_api_key_here
```
*(If no API key is provided, the C++ server seamlessly runs the deterministic local conversational fallback engine across all 4 languages without crashing or failing).*

### Single Command Launcher
Run both the C++ backend and the Vite frontend:
```bash
./run.sh
```

### Access Ports
- **Voice Assistant App**: `http://localhost:5173/`
- **C++ Backend Health**: `http://localhost:8000/api/health`

---

## 5. Verification and Tests

### C++ Core Unit Tests
```bash
cd backend_cpp/build
make -j$(nproc)
ctest --output-on-failure
```

### End-to-End Integration Tests
```bash
python3 scripts/test_cpp_voicebot_api.py
```

### Frontend Production Build
```bash
cd frontend && npm run build
```
