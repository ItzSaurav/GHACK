#!/usr/bin/env python3
"""
Lightweight Neural TTS Worker for Sahaay Voicebot.
Generates crystal-clear neural MP3 audio using edge-tts.
"""

import sys
import asyncio
import os

try:
    import edge_tts
except ImportError:
    sys.stderr.write("edge-tts not installed\n")
    sys.exit(1)

VOICE_MAP = {
    "hi": "hi-IN-MadhurNeural",
    "hi-in": "hi-IN-MadhurNeural",
    "en": "en-IN-PrabhatNeural",
    "en-in": "en-IN-PrabhatNeural",
    "gu": "gu-IN-DhwaniNeural",
    "gu-in": "gu-IN-DhwaniNeural",
    "mr": "mr-IN-AarohiNeural",
    "mr-in": "mr-IN-AarohiNeural",
}

async def main():
    if len(sys.argv) < 4:
        sys.stderr.write("Usage: tts_worker.py <text_file> <lang_code> <output_mp3_path>\n")
        sys.exit(1)

    text_file = sys.argv[1]
    raw_lang = sys.argv[2].lower()
    out_file = sys.argv[3]

    if not os.path.exists(text_file):
        sys.stderr.write(f"Text file not found: {text_file}\n")
        sys.exit(1)

    with open(text_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        sys.exit(0)

    voice = VOICE_MAP.get(raw_lang, VOICE_MAP.get(raw_lang.split("-")[0], "hi-IN-MadhurNeural"))
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)

    try:
        comm = edge_tts.Communicate(text, voice, rate="-2%")
        await comm.save(out_file)
    except Exception as e:
        if os.path.exists(out_file):
            try:
                os.remove(out_file)
            except OSError:
                pass
        sys.stderr.write(f"Edge-TTS synthesis error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
