#!/usr/bin/env python3
"""
Comprehensive test script for different audio formats with the transcription endpoint.
"""

import requests
import io
import wave
import numpy as np
import tempfile
import os
from pathlib import Path


def create_test_wav():
    """Create a simple test WAV file."""
    sample_rate = 16000
    duration = 2  # seconds
    frequency = 440  # Hz (A note)

    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    audio_data = (audio_data * 32767).astype(np.int16)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        with wave.open(temp_file.name, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        return temp_file.name


def create_test_webm():
    """Create a mock WebM file (just for testing MIME type handling)."""
    # Create a minimal WebM-like file for testing
    webm_header = b"\x1a\x45\xdf\xa3"  # WebM signature
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
        temp_file.write(webm_header)
        temp_file.write(b"\x00" * 1000)  # Dummy data
        return temp_file.name


def test_format(file_path, mime_type, model, description):
    """Test transcription with a specific format."""
    print(f"\n🧪 Testing {description}...")
    print(f"   File: {Path(file_path).name}")
    print(f"   MIME: {mime_type}")
    print(f"   Model: {model}")

    try:
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f, mime_type)}
            params = {"model": model}

            response = requests.post(
                "http://localhost:8000/transcribe_audio",
                files=files,
                params=params,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success! Model used: {result['model']}")
                if result["transcription"]:
                    print(f"   📝 Transcription: {result['transcription'][:100]}...")
                else:
                    print(f"   📝 Empty transcription (expected for test audio)")
                return True
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False

    except Exception as e:
        print(f"   💥 Exception: {str(e)}")
        return False


def main():
    """Run comprehensive format tests."""
    print("🎵 Audio Transcription Format Test Suite")
    print("=" * 50)

    # Create test files
    wav_file = create_test_wav()
    webm_file = create_test_webm()

    test_cases = [
        # Format: (file_path, mime_type, model, description)
        (
            wav_file,
            "audio/wav",
            "gpt-4o-transcribe",
            "WAV with gpt-4o-transcribe (should fallback)",
        ),
        (wav_file, "audio/wav", "whisper-1", "WAV with whisper-1 (direct)"),
        (webm_file, "audio/webm", "whisper-1", "WebM with whisper-1 (direct)"),
        (
            webm_file,
            "audio/webm",
            "gpt-4o-transcribe",
            "WebM with gpt-4o-transcribe (should fallback)",
        ),
    ]

    results = []

    try:
        for test_case in test_cases:
            success = test_format(*test_case)
            results.append((test_case[3], success))

    finally:
        # Cleanup
        os.unlink(wav_file)
        os.unlink(webm_file)

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)

    passed = 0
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {description}")
        if success:
            passed += 1

    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! The transcription system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")


if __name__ == "__main__":
    main()
