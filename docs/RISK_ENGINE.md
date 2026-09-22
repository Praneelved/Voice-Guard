# Risk Fusion Engine

VoiceGuard utilizes a deterministic, rule-based Risk Fusion Engine to evaluate calls. Rather than using an opaque machine learning fusion layer, the engine evaluates distinct signals (Anti-Spoofing AI, Speaker Verification, and Audio Quality) using weighted rules to produce explainable evidence codes.

## Core Rules

1. **Missing Speaker Enrollment Does Not Inflate Risk**
   - Unknown callers or calls lacking an `expected_speaker_id` will NOT have their risk inflated. The engine evaluates the anti-spoofing score independently.
2. **Poor Audio Reduces Confidence**
   - If `SileroVAD` or the quality analyzer detects extreme noise or clipping, the risk assessment `confidence` score is halved (e.g. `1.0` -> `0.5`), and the evidence `POOR_AUDIO_QUALITY` is attached.
3. **Spikes vs. Persistence (Temporal Tracking)**
   - A single anomalous window of high spoof probability (a spike) is recorded as `TRANSIENT_ANTISPOOF_SPIKE` but smoothed via Exponential Moving Average (EMA). It will not immediately push the call into `HIGH` risk.
4. **Minimum Evidence Gating**
   - No definitive risk is assigned until at least N valid windows have been processed (`min_valid_windows`). Until then, the state remains `COLLECTING`.

## Output Schema

The engine outputs a transparent `RiskAssessment` object containing the top-level score/level, alongside the raw signals and explicit evidence codes that triggered the decision:

```json
{
   "riskScore": 0.82,
   "riskLevel": "HIGH",
   "confidence": 0.86,
   "signals": {
      "antiSpoof": {
          "score": 0.88,
          "confidence": 0.91
      },
      "speakerVerification": {
          "available": true,
          "similarity": 0.31
      },
      "audioQuality": {
          "status": "GOOD"
      }
   },
   "evidence": [
      {
        "code": "PERSISTENT_ANTISPOOF_SIGNAL",
        "severity": "HIGH"
      },
      {
        "code": "EXPECTED_SPEAKER_MISMATCH",
        "severity": "MEDIUM"
      }
   ]
}
```

## Evidence Codes & Wording

We avoid definitive labels like "FAKE" or "SCAMMER". The evidence codes explicitly state the technical findings:

- `PERSISTENT_ANTISPOOF_SIGNAL` (HIGH): Anti-spoofing model has consistently flagged audio windows.
- `TRANSIENT_ANTISPOOF_SPIKE` (LOW): A single anomalous audio window was flagged, but not persistently.
- `EXPECTED_SPEAKER_MISMATCH` (MEDIUM/HIGH): The speaker's voice does not match the expected enrolled profile.
- `POOR_AUDIO_QUALITY` (LOW): Audio quality is too poor for reliable analysis.
- `INSUFFICIENT_EVIDENCE` (LOW): Not enough speech analyzed to form a reliable risk assessment.
- `NO_RISK_DETECTED` (LOW): All signals are normal.

Frontend interfaces should translate these into user-friendly warnings, such as: *"Potential synthetic voice characteristics detected."*
