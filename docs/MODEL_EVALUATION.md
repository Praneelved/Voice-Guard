# VoiceGuard Model Evaluation Guide

VoiceGuard provides a robust evaluation framework designed to scientifically test the efficacy of the underlying Anti-Spoofing and Speaker Verification models across realistic, degraded conditions.

## Philosophy

A model that achieves 99% accuracy on pristine, clean audio in a laboratory setting often fails completely when exposed to 8kHz μ-law encoded telephony with background noise. VoiceGuard's evaluation framework explicitly tests across these harsh, real-world conditions.

**Golden Rule:** Do not tune thresholds and evaluate metrics on the same subset of data. VoiceGuard enforces strict separation using `split` metadata.

## Using the Framework

### 1. Preparing the Dataset
The evaluation script (`evaluation/run_evaluation.py`) accepts metadata files in either `.csv` or `.jsonl` format. 

**Required Columns/Fields:**
- `filepath`: Absolute or relative path to the audio file.
- `label`: `"spoof"` (or `1`) vs `"genuine"` (or `0`).
- `split`: `"train"`, `"dev"`, or `"test"`. **The framework will only evaluate files marked as `test`.**

**Optional Metadata:**
- `language`: Used for demographic intersection testing.
- `attack_type`: Identifying TTS vs Voice Clone vs Replay.

*Example `dataset.csv`:*
```csv
filepath,label,split,language
/data/asvspoof/test/12049.wav,genuine,test,en
/data/asvspoof/test/18392.wav,spoof,test,en
```

### 2. Running an Evaluation
Run the pipeline pointing to your metadata file:

```bash
python -m evaluation.run_evaluation --metadata path/to/dataset.csv --out evaluation/results/
```

### 3. Understanding the Transformations
The evaluation harness automatically loops over three primary conditions:
1. **Clean**: No transformations applied. Matches laboratory benchmarks.
2. **Telephony**: Simulates PSTN/Twilio ingest. The audio is downsampled to 8kHz, encoded via G.711 μ-law, and injected with minor 2% packet-loss.
3. **Noisy Telephony**: Applies the Telephony transformations and layers Gaussian white noise (SNR = 10dB) to simulate calling from a crowded street.

### 4. Interpreting Results (`results.json`)

The output JSON provides metric stratification across the test conditions. 

- **EER (Equal Error Rate)**: The percentage where False Positives and False Negatives are perfectly balanced. *Lower is better.* EER is heavily utilized in biometrics.
- **ROC-AUC**: Area Under the Receiver Operating Characteristic Curve. Represents the probability the model will score a random spoof higher than a random genuine call. *1.0 is perfect.*
- **Operating Points**: The script simulates running the system in production at specific decision thresholds (e.g., `0.75` for HIGH risk). It calculates:
  - `precision` / `recall` / `f1`
  - `fpr` (False Positive Rate) - Critical for avoiding locking out legitimate users.
  - `fnr` (False Negative Rate) - Critical for security.

## Adding New Transformations
You can simulate new environments (e.g., specific compression codecs or reverberation) by adding functions to `evaluation/transforms.py` and hooking them into the `conditions` loop inside `run_evaluation.py`.
