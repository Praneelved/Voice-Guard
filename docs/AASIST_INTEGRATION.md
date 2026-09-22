# PyTorch AASIST Integration

VoiceGuard supports analyzing live audio streams using the AASIST architecture for detecting synthetic speech or spoofing artifacts. The integration strictly adheres to a zero-download and safe-inference architectural model.

## Configuration

To switch from the default `mock` provider to the real PyTorch engine, update your `.env` configuration:

```env
ANTISPOOF_PROVIDER=aasist
AASIST_MODEL_PATH=/path/to/local/aasist/model/dir
AI_DEVICE=auto
```

### Parameters
- **`ANTISPOOF_PROVIDER`**: Either `mock` or `aasist`.
- **`AASIST_MODEL_PATH`**: The local, absolute path to the directory containing the pre-downloaded AASIST model weights (e.g., HuggingFace format `config.json`, `pytorch_model.bin`). VoiceGuard enforces `local_files_only=True` to guarantee no hidden internet downloads occur at runtime.
- **`AI_DEVICE`**: Options are `auto`, `cuda`, `mps` (Apple Silicon), or `cpu`.

## Architecture Details

1. **Model Loading (Singleton)**: The AASIST detector is instantiated exactly once during startup (or the first API call requiring it). Re-loading for every incoming chunk is avoided to prevent massive performance bottlenecks.
2. **Missing Weights Fallback**: If `AASIST_MODEL_PATH` is unpopulated or invalid, the model gracefully fails to load but the application *does not crash*. Subsequent audio analyses will return safe fallbacks and log the failure.
3. **Inference Mode**: We use `torch.inference_mode()` which significantly reduces memory overhead and improves speed over `torch.no_grad()`.
4. **Concurrency & Event Loops**: VoiceGuard is built on FastAPI's async event loop. Since raw PyTorch inference blocks the thread, inference calls are wrapped in `asyncio.to_thread`. This allows multiple audio streams to process simultaneously without halting the ingestion of new Twilio frames.

## Audio Requirements

AASIST generally requires:
- **Sample Rate**: 16000 Hz
- **Channels**: Mono
- **Format**: Normalized `float32` arrays in the range `[-1.0, 1.0]`

The `services/audio/AudioPreprocessor` pipeline natively decodes Twilio μ-law, normalizes, resamples, and buffers it into 4-second overlapping chunks to perfectly fit the AASIST entry point.

## Terminology Limitations

AASIST provides a **spoof probability** and **synthetic-speech indicators**. It does *not* offer absolute proof that a caller is fake. The final decision is a combination of temporal persistence (analyzed by VoiceGuard's RiskEngine), audio quality metrics, and spoof confidence.

## Testing

For CI/CD and rapid testing, developers should leave `ANTISPOOF_PROVIDER=mock`. This returns instantaneous, simulated risk scores without requiring GPU hardware or large model downloads. To run the full integration test:
```bash
AASIST_MODEL_PATH=/path/to/model pytest tests/test_aasist_integration.py
```
