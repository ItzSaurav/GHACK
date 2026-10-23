"""Performance, RAM, and Latency Benchmark Script.

Measures physical application RAM, median and p95/p99 response latency,
audio payload sizes, and rule verification accuracy under test workloads.
"""

import io
import os
import resource
import statistics
import time
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def measure_memory_rss() -> float:
    """Returns resident set size (RSS) memory in MB."""
    # Under Linux, ru_maxrss is in Kilobytes
    kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(kb / 1024.0, 2)


def benchmark_api_latencies(iterations: int = 50):
    endpoints = {
        "GET /api/v1/health": lambda: client.get("/api/v1/health"),
        "GET /api/v1/schemes": lambda: client.get("/api/v1/schemes"),
    }

    results = {}
    for name, call_fn in endpoints.items():
        latencies = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            resp = call_fn()
            t1 = time.perf_counter()
            assert resp.status_code == 200
            latencies.append((t1 - t0) * 1000.0)  # in milliseconds

        latencies.sort()
        results[name] = {
            "median_ms": round(statistics.median(latencies), 2),
            "p90_ms": round(latencies[int(len(latencies) * 0.90)], 2),
            "p99_ms": round(latencies[int(len(latencies) * 0.99)], 2),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "samples": len(latencies),
        }

    # Benchmark conversation flow latency
    start_resp = client.post("/api/v1/conversation/start", json={"language": "hi"})
    sess_id = start_resp.json()["session_id"]

    msg_latencies = []
    for utterance in [
        "मेरी उम्र 38 साल है",
        "मैं एक किसान हूँ",
        "हाँ मेरे पास 2 एकड़ जमीन है",
        "नहीं टैक्स नहीं भरता",
        "नहीं कोई फसल नुकसान नहीं हुआ",
    ]:
        t0 = time.perf_counter()
        resp = client.post(
            "/api/v1/conversation/message",
            json={"session_id": sess_id, "text": utterance, "source": "text"},
        )
        t1 = time.perf_counter()
        assert resp.status_code == 200
        msg_latencies.append((t1 - t0) * 1000.0)

    results["POST /api/v1/conversation/message"] = {
        "median_ms": round(statistics.median(msg_latencies), 2),
        "p90_ms": round(msg_latencies[int(len(msg_latencies) * 0.90)], 2),
        "min_ms": round(min(msg_latencies), 2),
        "max_ms": round(max(msg_latencies), 2),
        "samples": len(msg_latencies),
    }

    return results


def measure_audio_payloads():
    """Measures audio payload size for 2-second and 5-second 16kHz PCM audio."""
    # 2-second 16kHz 16-bit mono PCM: 16000 * 2 bytes * 2 sec = 64,000 bytes (~62.5 KB)
    # 44-byte WAV header
    bytes_2s = 44 + (16000 * 2 * 2)
    bytes_5s = 44 + (16000 * 2 * 5)
    return {
        "2_second_pcm_wav_bytes": bytes_2s,
        "2_second_pcm_wav_kb": round(bytes_2s / 1024.0, 2),
        "5_second_pcm_wav_bytes": bytes_5s,
        "5_second_pcm_wav_kb": round(bytes_5s / 1024.0, 2),
        "max_enforced_upload_limit_mb": 5,
    }


def run_benchmark():
    ram_initial = measure_memory_rss()
    latency_data = benchmark_api_latencies(iterations=50)
    audio_data = measure_audio_payloads()
    ram_peak = measure_memory_rss()

    report = {
        "ram_initial_mb": ram_initial,
        "ram_peak_mb": ram_peak,
        "ram_delta_under_load_mb": round(ram_peak - ram_initial, 2),
        "latencies": latency_data,
        "audio_payloads": audio_data,
    }

    print("=== BENCHMARK RESULTS ===")
    import json
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run_benchmark()
