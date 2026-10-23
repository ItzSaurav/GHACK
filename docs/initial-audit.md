# Initial Audit and Feasibility Report

## 1. Executive Summary

This report establishes the baseline environment inspection, hardware limits, toolchain inventory, and architecture blueprint for the Voice-First Multilingual Government Scheme Assistant prototype.

The prototype is designed for low-literacy citizens seeking welfare access through voice or text in Indian languages (prioritizing Hindi and English/Hinglish for the primary release), supported by deterministic scheme eligibility rules, document checklists, and citizen-reviewed form assistance.

---

## 2. Environment and Hardware Verification

Physical verification conducted on 2026-10-23:

- Operating System: Linux 6.18.54-1-lts x86_64
- Hardware Platform: Intel Core i3-7100U CPU @ 2.40GHz (2 physical cores, 4 threads)
- System Memory:
  - Total RAM: 7.7 GiB
  - Free/Available RAM at audit time: 2.4 GiB (Active consumption: 5.3 GiB)
  - Swap: 7.7 GiB configured
- Disk Space: 375 GiB available on root partition (`/dev/sda2`)
- Hardware Constraints Assessment:
  - The host machine has limited available memory (~2.4 GiB) and a dual-core mobile CPU.
  - Large neural models (Whisper large/medium requiring 3-10 GiB VRAM or system RAM) are infeasible and would trigger Out-Of-Memory termination or severe swapping.
  - Architecture decision: Implement a pluggable dual-tier speech pipeline:
    1. Client-side browser Web Speech API (zero server memory, zero latency, native support for Indian English and Hindi).
    2. Server-side pluggable adapter interface with a lightweight audio validator, confidence scoring, and fallback acoustic engine.
    3. Seamless text-only fallback for low-bandwidth and offline environments.

---

## 3. Tooling and Runtime Inventory

- Python Runtime:
  - System default: Python 3.14.7 (pre-release)
  - Managed environment: Python 3.12.14 available via `uv` at `/home/saurav/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12`.
  - Python 3.12 is chosen for the backend virtual environment (`.venv`) for stable C-extensions, Pydantic v2, FastAPI, and Pytest.
- Package Managers & Build Tools:
  - `uv` 0.12.18: Installed and active.
  - Node.js: v24.21.0.
  - npm: 11.19.0.
  - ffmpeg: `/usr/bin/ffmpeg` verified.
  - Git: Initialized on `main` branch.
- Autonomous Decision Engine:
  - Jev System One decision engine: Available at `/home/saurav/.local/bin/jev` and `/home/saurav/.gemini/config/scripts/jev.js`.
  - Task complexity routing score: continuous score 3.72, Level 4 (High Rigor Engineering).
- External Coding Agents & Cloud APIs:
  - `opencode` CLI: Database and app files detected in user state, but no standalone binary in system PATH.
  - External paid API keys (OpenAI, Anthropic, Gemini, Groq): None configured in environment.
  - Decision: All workflows will run locally using free-tier / local infrastructure with zero hardcoded credentials and zero external payment dependencies.

---

## 4. Multi-Agent Orchestration Architecture

Antigravity operates as the lead integrator, technical architect, and QA supervisor. Native subagents and specialized modules are partitioned across strict boundaries:

- Agent A (Frontend & Accessibility):
  - Responsibilities: React + Vite + TypeScript interface, responsive design, audio capture state machine, big tactile controls, high contrast, multilingual toggle (Hindi/English), screen reader support, keyboard accessibility, transcript editing before submit.
  - Directory: `frontend/`
- Agent B (Backend & Secure API):
  - Responsibilities: FastAPI application, input sanitization, rate limiting, bounded request size, structured privacy-conscious logging (redacting personal values), health endpoints, CORS policies.
  - Directory: `backend/app/api/` and `backend/app/main.py`
- Agent C (Scheme Catalogue & Deterministic Eligibility Engine):
  - Responsibilities: Versioned JSON/SQLite scheme models, pure deterministic rule evaluation, missing-fact detection, explanation generators, document checklist mapping.
  - Boundaries: LLMs are strictly forbidden from acting as final eligibility arbiters.
  - Directory: `backend/app/schemes/`
- Agent D (Voice Pipeline & Multilingual Adapters):
  - Responsibilities: Pluggable ASR/TTS interfaces, browser speech bridge, audio format verification, transcript confidence checks, Hinglish/Hindi fact parsing.
  - Directory: `backend/app/voice/`
- Agent E (QA, Verification & Performance):
  - Responsibilities: Automated unit and integration test suites, boundary testing, security verification, real RAM and latency measurements under benchmark workloads.
  - Directory: `tests/` and `benchmarks/`

---

## 5. Implementation Phases and Quality Gates

1. Phase 1: Working Skeleton and Setup Documentation
   - Build FastAPI backend scaffold with health checks.
   - Setup React + Vite frontend scaffold with build validation.
   - Gate: Clean startup and passing baseline tests.

2. Phase 2: Deterministic Scheme Engine
   - Formalize Scheme schema (ID, name, department, state, criteria, required documents, source URLs, effective date, version).
   - Seed representative schemes (e.g., PM-KISAN, PM-SYM, PMMVY, Ayushman Bharat PM-JAY, State Farmer Assistance).
   - Implement rule evaluator returning `potential_match`, `not_matched`, `insufficient_information`, `manual_review`.
   - Gate: 100% passing tests for match, non-match, boundary conditions, and missing fields.

3. Phase 3: Conversational Flow and API
   - Interactive dialogue manager collecting one fact at a time.
   - Deterministic entity extractor for age, income, occupation, land ownership, residence, and gender.
   - Allow user corrections, back-tracking, and session resets.
   - Gate: Full end-to-end conversation flow without simulated backend responses.

4. Phase 4: Voice Pipeline
   - Audio capture with Web Audio API / MediaRecorder.
   - Web Speech API integration for zero-resource client-side transcription in Hindi and English.
   - Server-side pluggable ASR adapter with format validation and confidence scoring.
   - Pluggable TTS synthesizer and text fallback.
   - Gate: Voice input, transcript correction, and audio failure fallbacks verified.

5. Phase 5: Form Assistance and Allowlisted Autofill
   - Field mapping from confirmed conversation facts to allowlisted form schemas.
   - Preview step presenting all proposed values for citizen review.
   - Explicit confirmation requirement before generating final submission payload.
   - Gate: No automated submissions without citizen consent.

6. Phase 6: Security Audit, Benchmarking and Final Deliverables
   - Verification of input validation, privacy filters (no storage of Aadhaar, passwords, or bank data).
   - Real measurement of RAM consumption, response latency, and payload sizes.
   - Comprehensive documentation and user reference guide.
   - Gate: Clean test runs, zero critical security flaws, documented benchmarks.
