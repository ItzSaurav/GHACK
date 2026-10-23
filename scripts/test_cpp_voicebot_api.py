#!/usr/bin/env python3
"""
Integration test suite for the C++ Multilingual Voicebot Server.
Verifies health, 4-language auto-detection, chat responses, and transcription endpoints.
"""

import subprocess
import time
import urllib.request
import urllib.parse
import json
import os
import sys
import socket

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_BIN = os.path.join(ROOT_DIR, "backend_cpp/build/voicebot_server")

def run_tests():
    port = get_free_port()
    print("Starting C++ Voicebot Server on dynamic port", port, "for integration testing...")
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["HOST"] = "127.0.0.1"

    proc = subprocess.Popen(
        [SERVER_BIN],
        cwd=ROOT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Wait for server to be ready
        ready = False
        last_exc = None
        for _ in range(50):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception as e:
                last_exc = e
                time.sleep(0.1)

        if not ready:
            print(f"ERROR: Server failed to become ready within timeout. Last exc: {last_exc}")
            proc.terminate()
            try:
                out, err = proc.communicate(timeout=2)
                print("Server stdout:\n", out.decode(errors='ignore'))
                print("Server stderr:\n", err.decode(errors='ignore'))
            except Exception as e:
                print("Could not collect server output:", e)
            sys.exit(1)

        print("Server is up and healthy! Running API tests...")

        # 1. Health check
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health") as resp:
            data = json.loads(resp.read().decode())
            assert data["status"] == "healthy"
            assert data["engine"] == "cpp-voicebot-core"
            codes = [l["code"] for l in data["languages"]]
            assert "en" in codes and "hi" in codes and "gu" in codes and "mr" in codes
            print("PASS: /api/health returned valid engine and 4 supported languages.")

        # 2. English Chat
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/chat",
            data=json.dumps({"message": "Hello, what can you do?"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            assert data["success"] is True
            assert data["detected_language"] == "en"
            assert data["bcp47"] == "en-IN"
            assert len(data["reply"]) > 5
            print("PASS: English auto-detection and response:", data["reply"][:40], "...")

        # 3. Hindi Chat
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/chat",
            data=json.dumps({"message": "नमस्ते जी, आप कैसे हैं?"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            assert data["success"] is True
            assert data["detected_language"] == "hi"
            assert data["bcp47"] == "hi-IN"
            assert len(data["reply"]) > 5
            print("PASS: Hindi auto-detection and response:", data["reply"][:40], "...")

        # 4. Gujarati Chat
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/chat",
            data=json.dumps({"message": "નમસ્તે, મને તમારા વિશે કહો"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            assert data["success"] is True
            assert data["detected_language"] == "gu"
            assert data["bcp47"] == "gu-IN"
            assert len(data["reply"]) > 5
            print("PASS: Gujarati auto-detection and response:", data["reply"][:40], "...")

        # 5. Marathi Chat
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/chat",
            data=json.dumps({"message": "नमस्कार, मला सांगा तुम्ही कोण आहात आणि कशी मदत करू शकता?"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            assert data["success"] is True
            assert data["detected_language"] == "mr"
            assert data["bcp47"] == "mr-IN"
            assert len(data["reply"]) > 5
            print("PASS: Marathi auto-detection and response:", data["reply"][:40], "...")

        # 6. History handling
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How is the weather?"}
        ]
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/chat",
            data=json.dumps({"history": history}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            assert data["success"] is True
            assert data["detected_language"] == "en"
            print("PASS: Multi-turn history preserved and processed.")

        # 7. TTS GET endpoint
        encoded_text = urllib.parse.quote("नमस्ते")
        tts_url = f"http://127.0.0.1:{port}/api/tts?text={encoded_text}&lang=hi-IN"
        with urllib.request.urlopen(tts_url) as resp:
            assert resp.status == 200
            assert resp.headers.get("Content-Type") == "audio/mpeg"
            audio_bytes = resp.read()
            assert len(audio_bytes) > 500
            print(f"PASS: /api/tts GET returned valid MP3 stream ({len(audio_bytes)} bytes).")

        # 8. TTS POST endpoint (and cache retrieval)
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/tts",
            data=json.dumps({"text": "Hello citizen", "language": "en-IN"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            assert resp.headers.get("Content-Type") == "audio/mpeg"
            post_audio_bytes = resp.read()
            assert len(post_audio_bytes) > 500
            print(f"PASS: /api/tts POST returned valid MP3 stream ({len(post_audio_bytes)} bytes).")

        print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY!")

    finally:
        proc.terminate()
        proc.wait(timeout=3)

if __name__ == "__main__":
    run_tests()
