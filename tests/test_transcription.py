#!/usr/bin/env python3
"""
Test script for the transcription endpoint with fallback mechanism.
"""

import requests
import io
import wave
import numpy as np
import tempfile
import os


def create_test_audio():
    """Create a simple test WAV file."""
    # Generate a simple sine wave
    sample_rate = 16000
    duration = 2  # seconds
    frequency = 440  # Hz (A note)

    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3

    # Convert to 16-bit integers
    audio_data = (audio_data * 32767).astype(np.int16)

    # Create WAV file in memory
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        with wave.open(temp_file.name, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        return temp_file.name


def test_transcription_endpoint():
    """Test the transcription endpoint."""
    # Create test audio file
    audio_file_path = create_test_audio()

    try:
        # Test with gpt-4o-transcribe (should fallback to whisper-1)
        print("Testing transcription with gpt-4o-transcribe...")

        with open(audio_file_path, "rb") as f:
            files = {"file": ("test_audio.wav", f, "audio/wav")}
            params = {"model": "gpt-4o-transcribe"}

            response = requests.post(
                "http://localhost:8000/transcribe_audio", files=files, params=params
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! Model used: {result['model']}")
                print(f"Transcription: {result['transcription']}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")

        # Test with whisper-1 directly
        print("\nTesting transcription with whisper-1...")

        with open(audio_file_path, "rb") as f:
            files = {"file": ("test_audio.wav", f, "audio/wav")}
            params = {"model": "whisper-1"}

            response = requests.post(
                "http://localhost:8000/transcribe_audio", files=files, params=params
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! Model used: {result['model']}")
                print(f"Transcription: {result['transcription']}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")

    finally:
        # Clean up
        os.unlink(audio_file_path)


if __name__ == "__main__":
    test_transcription_endpoint()
