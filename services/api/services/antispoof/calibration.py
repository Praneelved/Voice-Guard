def calibrate_probability(raw_spoof_prob: float) -> float:
    """
    Standardize raw AASIST logit/probability output into a VoiceGuard risk metric (0.0 - 1.0).
    AASIST probability might require scaling or shifting based on validation distributions.
    """
    # For now, return the probability clamped to [0, 1]
    return max(0.0, min(1.0, raw_spoof_prob))
