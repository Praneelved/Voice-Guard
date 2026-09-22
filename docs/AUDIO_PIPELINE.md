# VoiceGuard Audio Pipeline

This document describes the audio transformation pipeline in VoiceGuard. The pipeline is designed to ingest raw payload packets from a telephony provider (Twilio), clean and analyze them, and emit them as uniform, high-quality tensors ready for AI inference.

## Overview

The audio pipeline resides in `services/api/services/audio` and processes streaming data incrementally. It ensures that the anti-spoofing and speaker verification models only receive valid speech, preventing false positives from silence, static, or malformed packets.

### Pipeline Stages

1. **Twilio Media Payload (Base64)**
   - The provider webhook adapter receives a JSON message containing base64-encoded audio payload.

2. **Decoding (`decoder.py`)**
   - The payload is base64-decoded into raw bytes.
   - Twilio uses G.711 μ-law encoding at 8000 Hz. The `audioop` module expands this to 16-bit linear PCM (`np.int16`).

3. **Resampling & Normalization (`resampler.py`)**
   - The 16-bit PCM array is converted to 32-bit floating point (`float32`).
   - The values are normalized to a range of approximately `[-1.0, 1.0]`.
   - The audio is converted to Mono (if not already).
   - `librosa` resamples the 8000 Hz stream up to 16000 Hz, which is the standard sample rate expected by most modern audio deep learning models (including Silero VAD, AASIST, and ECAPA-TDNN).

4. **Voice Activity Detection (`vad.py`)**
   - The 16kHz float32 chunk is passed through Silero VAD (loaded via PyTorch Hub).
   - If the chunk contains silence, it is discarded. Only voiced chunks proceed to the buffer.

5. **Rolling Speech Buffer (`buffer.py`)**
   - Voiced chunks are accumulated in a rolling buffer.
   - When the buffer reaches the `ANALYSIS_WINDOW_SECONDS` (default: 4 seconds), a copy of the window is extracted and passed to the next stage.
   - The buffer slides forward by `ANALYSIS_STRIDE_SECONDS` (default: 1 second) to create overlapping analysis windows.

6. **Quality Analysis (`quality.py`)**
   - The extracted window is evaluated for quality heuristics.
   - Metrics calculated:
     - **RMS Energy**: Ensures the audio isn't too quiet.
     - **Clipping Ratio**: Ensures the audio isn't heavily distorted.
     - **Voiced Ratio**: Confirms the window has sufficient speech.
   - If the window fails quality gating, it is flagged as `INSUFFICIENT_AUDIO_QUALITY`.

7. **Risk Engine & AI Orchestration (`preprocessing.py` & `router.py`)**
   - The orchestrator yields the float32 tensor and the quality dictionary.
   - If the quality is insufficient, the system bypasses the AI inference to save compute resources and prevent random/unreliable predictions, injecting a "poor quality" signal into the Risk Engine.

## Configuration

The pipeline is configurable via environment variables:

- `AUDIO_ANALYSIS_WINDOW_SECONDS`: The duration of each audio window passed to the AI (default: 4).
- `AUDIO_ANALYSIS_STRIDE_SECONDS`: The overlap stride (default: 1).
