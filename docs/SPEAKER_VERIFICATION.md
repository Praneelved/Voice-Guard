# Speaker Verification (ECAPA-TDNN)

VoiceGuard implements optional speaker verification using the `speechbrain/spkrec-ecapa-voxceceb` model.

## Purpose

The Speaker Verification feature answers the question: **"How similar is the current caller's voice to a previously enrolled trusted voice?"**
It does *not* detect if the voice is synthetic or spoofed. It only verifies identity.

## Enrollment

Users can enroll "Trusted Voices" via the frontend (React Native application).
The enrollment process:
1. The user speaks multiple short phrases into the mobile app.
2. The frontend POSTs base64-encoded audio samples to `/v1/trusted-voices/{id}/samples`.
3. The backend preprocesses the audio, uses Silero VAD to ensure sufficient high-quality speech exists, and extracts a 192-dimensional vector embedding for each sample.
4. The embeddings are stored in PostgreSQL using the `ARRAY(Float)` type.

## Verification

During an active Twilio call, verification only occurs if an `expected_speaker_id` is supplied in the Twilio stream initialization payload.
**VoiceGuard does not continuously scan every caller against a global database.** This is by design, limiting unnecessary compute and protecting privacy.

When an `expected_speaker_id` is present:
1. The live 4-second audio window is encoded into a live embedding.
2. The live embedding is compared against all stored embeddings for the expected speaker using **Cosine Similarity**.
3. A similarity score between `0.0` and `1.0` is computed.
4. If the score exceeds the configurable `SIMILARITY_THRESHOLD` (default 0.40), the payload includes `matchState: LIKELY_MATCH`.

## Privacy Implications

- **Biometric Retention**: The stored embeddings are essentially biometric signatures. VoiceGuard stores them in `voice_embeddings` securely. 
- **Deletion**: Users have full control over their data and can issue a `DELETE /v1/trusted-voices/{id}` request to permanently wipe the profile and all associated embeddings from PostgreSQL.
- **Opt-In Verification**: As stated, the system only attempts verification against a specific ID when explicitly asked, avoiding continuous dragnet surveillance of all callers.
