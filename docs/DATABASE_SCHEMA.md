# VoiceGuard Database Schema

## Overview
PostgreSQL (managed via Supabase) will be the primary persistent data store.

### Table: `users`
- `id` (UUID, Primary Key)
- `email` (String, Unique)
- `name` (String)
- `organization_id` (UUID, Nullable, Foreign Key)
- `created_at` (Timestamp)

### Table: `user_settings`
- `user_id` (UUID, Primary Key, Foreign Key to `users`)
- `privacy_level` (String: 'strict', 'standard')
- `block_high_risk` (Boolean)
- `notifications_enabled` (Boolean)
- `updated_at` (Timestamp)

### Table: `calls`
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to `users`)
- `provider_call_id` (String, Unique from SIP provider)
- `caller_number` (String)
- `started_at` (Timestamp)
- `ended_at` (Timestamp, Nullable)
- `status` (String: 'active', 'completed', 'failed')
- `max_risk_score` (Float)
- `spoof_detected` (Boolean)

### Table: `call_events` (Optional/Archival)
*Used for auditing and detailed history, potentially rolled off to cold storage.*
- `id` (UUID, Primary Key)
- `call_id` (UUID, Foreign Key to `calls`)
- `timestamp` (Timestamp)
- `event_type` (String: 'risk_spike', 'spoof_flag', 'user_challenged')
- `metadata` (JSONB)

### Table: `voice_profiles` (Trusted Voices)
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to `users`)
- `name` (String, e.g., "CEO", "Spouse")
- `embedding_vector` (Vector/Array of Floats - ECAPA-TDNN embedding)
- `status` (String: 'enrolled', 'pending')
- `created_at` (Timestamp)

## Cache & Ephemeral State (Redis)
- **Active Call State:** Hash maps tracking active calls by `provider_call_id`.
- **Rolling Risk Windows:** Time-series data / lists maintaining the last N seconds of risk scores for active calls.
- **WebSocket Sessions:** Mapping of `user_id` to active WebSocket connection IDs for message routing.
