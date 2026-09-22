# Current VoiceGuard Audio Flow

The audio ingestion and analysis pipeline currently operates in the following sequence:

1. **Twilio (Provider)**
   - Sends base64-encoded μ-law audio frames over a WebSocket connection.
2. **WebSocket Ingestion (`services/api/services/stream_ingest/router.py`)**
   - `websocket_provider_endpoint` accepts the connection.
   - Parses media events using `TwilioProgrammableVoiceAdapter`.
   - Pushes raw audio data into an `ingest_queue`.
3. **Audio Pipeline (`services/api/services/audio_pipeline/pipeline.py`)**
   - An asynchronous worker pulls from `ingest_queue` and pushes to `AudioPipeline.push_chunk()`.
4. **Windowing & Preprocessing (`services/api/services/audio_pipeline/windowing.py` & `vad.py`)**
   - `WindowManager` buffers audio and extracts overlapping 3-second windows (16kHz PCM16).
   - `VoiceActivityDetector` analyzes speech ratio.
   - `analyze_quality` computes SNR/quality metrics.
5. **Mock Inference (`services/api/services/antispoof/detector.py`)**
   - `AudioPipeline._process_window` emits the window back to `router.py`.
   - `ai_worker` thread pulls the window and calls `antispoof_detector.predict()`.
   - Currently, this uses `MockAntiSpoofDetector` which generates random scores.
6. **Risk Engine (`services/api/services/risk_engine/engine.py`)**
   - `RiskEngine.process_window()` receives the mock scores.
   - Applies Exponential Moving Average (EMA) smoothing and quality gating.
   - Determines the current `RiskState` (LOW, CAUTION, HIGH).
7. **WebSocket Broadcast (`services/api/core/redis_client.py`)**
   - A `RiskUpdateEvent` is built and published via Redis pub/sub (`publish_event`).
8. **React Native (Mobile Client)**
   - The frontend listens to the WebSocket, receiving the `RiskUpdateEvent` and dynamically updating the UI.


# Existing Mock Components

Before integrating the real AI, the following mock implementations must be addressed:

1. **`services/api/services/antispoof/detector.py`**
   - **`MockAntiSpoofDetector.predict()`**: Generates random spoof probabilities using `np.random.uniform(0.1, 0.3)` or hardcodes `0.5` if the window is silent.
   
2. **`services/api/services/antispoof/__init__.py`**
   - Likely instantiates and returns `MockAntiSpoofDetector` via the `get_detector()` factory function.

3. **`services/api/api/routes/speakers.py`**
   - **`get_speakers()`**: Returns hardcoded `mock_speakers` imported from `core.sessions.py`.

4. **`services/api/services/stream_ingest/router.py`**
   - Hardcodes `DUMMY_ORG_ID = "00000000-0000-0000-0000-000000000000"` when persisting calls to the database.
   - `speaker_mismatch` and `signal_anomaly` scores are hardcoded to `None` when calling `risk_engine.process_window()`.


# Real AI Integration Plan

To replace the mock inference with actual deep learning models, we will execute the following minimum modifications:

1. **Activate the AASIST Model**
   - The `AASISTDetector` class already exists in `detector.py` and relies on `transformers` and `torch`. 
   - We will update `services/api/services/antispoof/__init__.py` to return the `AASISTDetector` instead of the `MockAntiSpoofDetector`.
   
2. **Implement Speaker Verification (ECAPA-TDNN)**
   - Create `services/api/services/speaker/verifier.py` to handle voice enrollments and speaker matching using an embedding model (e.g., SpeechBrain ECAPA-TDNN).
   - Update `api/routes/speakers.py` to accept audio uploads, generate embeddings, and persist them to Supabase (using pgvector).

3. **Feed Multi-Modal Signals to the Risk Engine**
   - In `router.py`, run both the `AASISTDetector` and the new `SpeakerVerifier` concurrently within the `ai_worker`.
   - Pass the resulting `spoof_probability` and `speaker_mismatch` scores into `risk_engine.process_window()`.

4. **Temporal Smoothing & Calibration**
   - Ensure the Risk Engine's EMA (`config.ema_alpha`) is tuned for the actual variance of the PyTorch models.
   - Add a calibration step in `AASISTDetector` to map raw logits to a strictly bounded probability [0, 1].


### FILES THAT WILL BE MODIFIED
- `services/api/services/antispoof/__init__.py` (Switch to real detector)
- `services/api/services/stream_ingest/router.py` (Add speaker matching to the pipeline loop)
- `services/api/api/routes/speakers.py` (Implement actual database queries and embedding generation)
- `services/api/services/risk_engine/config.py` (Tune thresholds for real AI outputs)

### FILES THAT WILL BE CREATED
- `services/api/services/speaker/verifier.py` (PyTorch ECAPA-TDNN embedding extractor and cosine similarity matcher)
- `services/api/api/routes/enrollment.py` (New endpoints to handle raw audio uploads from the mobile app)

### DEPENDENCIES REQUIRED
- `torch`, `torchaudio`, `transformers` (Already present in `requirements.txt`)
- `speechbrain` (Required for ECAPA-TDNN speaker verification)
- `psycopg2-binary` or `asyncpg` (Already present for database)

### RISKS / COMPATIBILITY ISSUES
- **Latency / Blocking**: PyTorch inference must be strictly offloaded to thread pools (`asyncio.to_thread`) to prevent blocking the async FastAPI event loop. If inference takes longer than 3 seconds (the window stride), the queue will overflow.
- **Memory Consumption**: Loading both `AASIST` and `ECAPA-TDNN` simultaneously on local/development machines might cause OOM (Out of Memory) issues depending on RAM availability.
- **Hardware Acceleration**: Ensuring `MPS` (Apple Silicon) or `CUDA` is correctly utilized by both models to maintain real-time performance.

### IMPLEMENTATION ORDER
1. Update `antispoof/__init__.py` to swap the Mock detector for `AASISTDetector` and verify live streaming performance.
2. Install `speechbrain` and implement `services/api/services/speaker/verifier.py`.
3. Create the trusted voice enrollment endpoints and wire them up to the React Native app.
4. Integrate the `speaker_mismatch` score into the live streaming pipeline (`router.py`) and Risk Engine.
5. Remove mock data modules (`core/sessions.py`).
