# Call Routing and Ownership

This document describes how VoiceGuard maps incoming telecom calls to authenticated users, ensuring that live risk assessment streams are only broadcast to authorized mobile clients.

## Problem Statement

When Twilio receives an inbound call, it fires a webhook to the VoiceGuard backend. At this point, the backend only knows the caller's phone number (`From`) and the VoiceGuard Twilio phone number (`To`). 

The VoiceGuard system needs to know **which authenticated user** owns the `To` number so it can:
1. Initialize the correct `CallSession` assigned to that user's organization.
2. Store risk analysis events securely against that user's account.
3. Broadcast live WebSocket updates *only* to mobile apps authenticated as that user.

## Architecture

We resolve call ownership through three primary components:

### 1. The `ProtectedNumber` Entity
Each telecom number provisioned for VoiceGuard is associated with an authenticated user via the `protected_numbers` table.

```python
class ProtectedNumber(Base):
    __tablename__ = 'protected_numbers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    provider = Column(String, nullable=False)
    provider_number = Column(String, nullable=False)
```

### 2. TwiML Webhook Routing
When Twilio calls `POST /v1/providers/twilio/webhook`, the router:
1. Extracts the `To` number.
2. Queries the `protected_numbers` table to find the associated `user_id`.
3. If no mapping exists (or the number is disabled), the backend returns a `<Reject/>` TwiML response, terminating the call immediately.
4. If a mapping exists, the backend returns `<Connect><Stream>` TwiML, and injects the `user_id` as a `<Parameter>`.

### 3. Media Stream Initialization
When the Twilio Media Stream connects to the backend WebSocket (`wss://.../ws/twilio`), it sends an initial `start` message.
- This message contains the `customParameters` we injected during the webhook phase.
- The `TwilioProgrammableVoiceAdapter` extracts the `user_id`.
- The `websocket_provider_endpoint` uses this `user_id` to create a `CallSession` assigned to that specific user (serving as their personal organization ID).

```python
user_id = adapter.custom_parameters.get("user_id")
if not user_id:
    logger.warning("Stream started without a user_id parameter. Dropping stream.")
    await websocket.close(code=1008)
    break

# Creates a session scoped to the user
call_session = await repo.create_call_session(org_id=uuid.UUID(user_id))
```

## Security Guarantees

By injecting the `user_id` into the TwiML stream parameters, we guarantee that the audio stream is inherently bound to the user who owns the destination phone number. 
Future risk evaluations query the `CallSession` to determine which `org_id` the event belongs to, making it impossible for events to leak to other tenants. Only authenticated mobile clients whose JWT `sub` or `org_id` matches the session's `org_id` will receive live Risk WebSocket events.
