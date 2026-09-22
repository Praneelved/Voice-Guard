EVIDENCE_CODES = {
    "PERSISTENT_ANTISPOOF_SIGNAL": {
        "description": "Anti-spoofing model has consistently flagged audio windows.",
        "severity": "HIGH"
    },
    "TRANSIENT_ANTISPOOF_SPIKE": {
        "description": "A single anomalous audio window was flagged, but not persistently.",
        "severity": "LOW"
    },
    "EXPECTED_SPEAKER_MISMATCH": {
        "description": "The speaker's voice does not match the expected enrolled profile.",
        "severity": "MEDIUM" # Or HIGH depending on strictness
    },
    "POOR_AUDIO_QUALITY": {
        "description": "Audio quality is too poor for reliable analysis.",
        "severity": "LOW"
    },
    "INSUFFICIENT_EVIDENCE": {
        "description": "Not enough speech analyzed to form a reliable risk assessment.",
        "severity": "LOW"
    },
    "NO_RISK_DETECTED": {
        "description": "All signals are normal.",
        "severity": "LOW"
    }
}
