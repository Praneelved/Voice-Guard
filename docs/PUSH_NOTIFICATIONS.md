# Push Notifications in VoiceGuard

VoiceGuard employs push notifications to alert users of potential voice spoofing or AI synthesis during an active call. 
This document outlines the architecture, flow, and testing procedures for push notifications.

## Architecture

Push notifications are orchestrated using the **Expo Push Notifications** framework. This avoids the need for maintaining separate APNs/FCM server keys, relying instead on Expo's unified delivery system.

### Database Schema
We maintain a `user_devices` table to store multiple device push tokens for a single authenticated user.
- **Fields**: `id`, `user_id`, `push_token`, `platform`, `enabled`, `last_seen_at`.

### Mobile Application (React Native / Expo)
1. **Permission Request**: When a user logs in, the `_layout.tsx` effect triggers `PushNotificationService.registerForPushNotificationsAsync()`.
2. **Token Generation**: The app requests the `ExpoPushToken` using `Notifications.getExpoPushTokenAsync()`.
3. **Backend Registration**: The token is sent to the backend via `POST /v1/users/devices`.
4. **Foreground Handler**: If a notification arrives while the app is open, we display a heads-up alert.
5. **Tap Handler**: Tapping the notification deep-links the user to `/call/live`.

### Backend Engine
1. **Detection**: `RiskFusionEngine` continuously analyzes audio windows inside the `TwilioProgrammableVoiceAdapter` processing loop.
2. **Trigger**: When an evaluation resolves to a `HIGH` Risk Level, the engine checks Redis for a cooldown key (`alert_cooldown:{call_id}`).
3. **Cooldown Logic**: 
   - If the key exists, the alert is suppressed (throttled).
   - If the key doesn't exist, an asynchronous request is dispatched to Expo (`https://exp.host/--/api/v2/push/send`) targeting all active tokens for that user.
   - The cooldown key is then set with a `60-second` expiry. This prevents notification spam during fluctuating signal predictions.

## Privacy Guarantee

Push notifications intentionally **do not** include any raw transcriptions, user audio snippets, or exact PII. 
The payload is strictly limited to:
- `title`: VoiceGuard Security Alert
- `body`: Elevated voice authenticity risk detected on your active call. Verify the caller before taking sensitive action.
- `data`: `call_id` and `type` (for routing).

## Development Testing

To test push notifications locally or on a physical device:

1. **EAS Project ID**: Ensure your `app.json` contains a valid EAS Project ID under `expo.extra.eas.projectId`. If using Expo Go, you must link your project to your Expo account via `eas init`.
2. **Physical Device**: Expo Push Notifications *do not* work on iOS Simulators, and require a physical device or a configured Android Emulator with Google Play Services.
3. **Mocking HIGH Risk**: You can artificially trigger a `HIGH` risk state by dialing into the Twilio number and playing a known synthetic sample, or by temporarily lowering the `RiskConfig.high_risk_threshold` in `services/api/services/risk/thresholds.py`.
4. **Observe Logs**: The backend will output `Triggering push notification for call {call_id} (HIGH risk)`. Ensure the mobile device receives the push shortly after.
