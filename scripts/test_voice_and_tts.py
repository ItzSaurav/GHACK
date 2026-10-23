import os
import time

# 1. Navigate to portal
goto_url("http://localhost:5173/")
wait_for_load()
time.sleep(2)

print("Page loaded. Testing Audio Recognition and TTS...")

# 2. Test TTS endpoint from browser context
print("\n--- 1. Testing Neural TTS Endpoint via Browser Fetch ---")
tts_fetch_result = js("""(async () => {
    try {
        const text = encodeURIComponent("नमस्ते! मैं आपका सहायक हूँ।");
        const res = await fetch(`/api/v1/voice/tts?text=${text}&language=hi`);
        const blob = await res.blob();
        return {
            status: res.status,
            contentType: res.headers.get("content-type"),
            byteSize: blob.size,
            ok: res.ok
        };
    } catch (e) {
        return { error: String(e) };
    }
})()""")
print("TTS Fetch Result:", tts_fetch_result)

# 3. Test HTML5 Audio Playability in Browser
print("\n--- 2. Testing HTML5 Audio Element Playability ---")
audio_play_result = js("""(async () => {
    return new Promise((resolve) => {
        const text = encodeURIComponent("नमस्ते");
        const audio = new Audio(`/api/v1/voice/tts?text=${text}&language=hi`);
        audio.oncanplaythrough = () => {
            resolve({
                canPlay: true,
                duration: audio.duration,
                readyState: audio.readyState
            });
        };
        audio.onerror = (err) => {
            resolve({ canPlay: false, error: "Audio failed to load" });
        };
        // Timeout after 5 seconds
        setTimeout(() => resolve({ canPlay: false, timeout: true }), 5000);
    });
})()""")
print("HTML5 Audio Playability:", audio_play_result)

# 4. Test Backend Voice Recognition via Browser Audio Upload
print("\n--- 3. Testing Microphone Audio Upload & ASR Pipeline ---")
asr_result = js("""(async () => {
    try {
        // Start conversation
        const startRes = await fetch("/api/v1/conversation/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ language: "hi" }),
        });
        const startData = await startRes.json();
        
        // Generate a 1-second 16kHz PCM WAV audio buffer (tone with acoustic energy)
        const sampleRate = 16000;
        const numSamples = sampleRate * 1;
        const buffer = new ArrayBuffer(44 + numSamples * 2);
        const view = new DataView(buffer);
        // RIFF chunk
        view.setUint32(0, 0x52494646, false); // "RIFF"
        view.setUint32(4, 36 + numSamples * 2, true);
        view.setUint32(8, 0x57415645, false); // "WAVE"
        // fmt chunk
        view.setUint32(12, 0x666d7420, false); // "fmt "
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true); // PCM
        view.setUint16(22, 1, true); // Mono
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true);
        view.setUint16(34, 16, true);
        // data chunk
        view.setUint32(36, 0x64617461, false); // "data"
        view.setUint32(40, numSamples * 2, true);
        // Add audible non-silent waveform
        for (let i = 0; i < numSamples; i++) {
            const s = Math.sin(2 * Math.PI * 440 * (i / sampleRate)) * 8000;
            view.setInt16(44 + i * 2, s, true);
        }
        
        const blob = new Blob([buffer], { type: "audio/wav" });
        const formData = new FormData();
        formData.append("session_id", startData.session_id);
        formData.append("language", "hi");
        formData.append("audio", blob, "test_mic.wav");
        
        const voiceRes = await fetch("/api/v1/conversation/voice", {
            method: "POST",
            body: formData,
        });
        return await voiceRes.json();
    } catch (e) {
        return { error: String(e) };
    }
})()""")
print("ASR Voice Pipeline Result:", asr_result)

# 5. Test Widget UI Elements
print("\n--- 4. Testing Widget UI Buttons & Microphone Interaction ---")
# Open widget
js("document.querySelector('.sahaay-launcher-btn')?.click()")
time.sleep(1)

# Check sound toggle button
sound_toggle_text = js("document.querySelector('.sound-toggle-btn')?.innerText")
print("Sound Toggle Button Text:", sound_toggle_text)

# Check mic button
mic_btn = js("Boolean(document.querySelector('.mic-button'))")
print("Tactile Mic Button Found in DOM:", mic_btn)

# Click Sound Toggle (mute then un-mute)
js("document.querySelector('.sound-toggle-btn')?.click()")
time.sleep(0.5)
sound_muted_text = js("document.querySelector('.sound-toggle-btn')?.innerText")
print("Sound Toggle Text after click:", sound_muted_text)
js("document.querySelector('.sound-toggle-btn')?.click()")
time.sleep(0.5)

# 6. Capture Verification Screenshot
os.makedirs("docs/screenshots", exist_ok=True)
capture_screenshot("docs/screenshots/live_voice_verified.png")
print("\nVerification screenshot captured: docs/screenshots/live_voice_verified.png")
print("=== VOICE & TTS PHYSICAL VERIFICATION COMPLETED ===")
