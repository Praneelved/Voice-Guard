# Authentication & Tenant Isolation

VoiceGuard uses **Supabase Auth** to secure all backend API endpoints and manage user sessions on the frontend. This ensures that users can only access their own calls, alerts, and enrolled trusted voices.

## Architecture

1. **Frontend (React Native + Expo)**
   - Uses the official `@supabase/supabase-js` client.
   - Sessions are securely persisted across app restarts using `@react-native-async-storage/async-storage`.
   - The `useAuthStore` (Zustand) automatically hydrates session state on app load. If a user is not authenticated, they are blocked at a loading screen or redirected to the login flow.
   - The `apiClient` automatically attaches the active Supabase JWT to the `Authorization: Bearer <token>` header of every outgoing REST request.
   - The `CallWebSocketClient` attaches the token as a query parameter (`?token=<token>`) when establishing the live risk streaming connection.

2. **Backend (FastAPI)**
   - Exposes a `get_current_user` dependency in `core/security.py`.
   - Endpoints requiring auth inject `current_user = Depends(get_current_user)`.
   - The backend directly decodes and verifies the JWT signature using `PyJWT` against the `SUPABASE_JWT_SECRET`. It does *not* make a network request to Supabase on every API call, ensuring low latency.
   - The `sub` claim inside the JWT is extracted, which corresponds to the user's UUID.

## Tenant Isolation

Since the FastAPI backend connects to the PostgreSQL database via SQLAlchemy (using a direct, high-privilege connection string), Supabase's native Row Level Security (RLS) policies that rely on `auth.uid()` do not automatically apply.

Therefore, **Tenant Isolation is enforced at the Application Layer**.

- Every database query (SELECT, UPDATE, DELETE) explicitly includes a `where(org_id == current_user["id"])` clause.
- When a user logs in for the very first time, the `get_current_user` dependency intercepts the request, checks if a corresponding `Organization` exists for that UUID, and automatically provisions a "Personal Org" if it doesn't. This satisfies the database foreign key constraints without requiring complex Postgres trigger migrations.

## Environment Variables

To properly configure the authentication flow, ensure the following environment variables are set:

**Frontend (`apps/mobile/.env`):**
```
EXPO_PUBLIC_SUPABASE_URL=https://<your-project>.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
```

**Backend (`services/api/.env`):**
```
SUPABASE_JWT_SECRET=<your-jwt-secret>
```

## Testing

A dedicated test suite is provided in `tests/test_auth_isolation.py`. This suite automatically generates signed JWTs using the local secret and verifies:
- Missing, Invalid, and Expired tokens are immediately rejected (`401 Unauthorized`).
- User A can create and retrieve their own calls and trusted voices.
- User B receives empty lists or `404 Not Found` when attempting to access User A's resources.
