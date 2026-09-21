import { AppState, AppStateStatus } from 'react-native';
import { CONFIG } from '../../constants/config';
import { WsEvent, ConnectionState } from '../../types';

export class CallWebSocketClient {
  private ws: WebSocket | null = null;
  private callId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private appStateSubscription: any = null;
  private intentionalDisconnect = false;

  constructor(
    private onEvent: (event: WsEvent) => void,
    private onStateChange: (state: ConnectionState) => void
  ) {
    this.handleAppStateChange = this.handleAppStateChange.bind(this);
  }

  public connect(callId: string) {
    this.callId = callId;
    this.intentionalDisconnect = false;
    this.reconnectAttempts = 0;
    
    if (!this.appStateSubscription) {
      this.appStateSubscription = AppState.addEventListener('change', this.handleAppStateChange);
    }
    
    this.establishConnection();
  }

  public disconnect() {
    this.intentionalDisconnect = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.appStateSubscription) {
      this.appStateSubscription.remove();
      this.appStateSubscription = null;
    }
    this.closeSocket();
    this.onStateChange('DISCONNECTED');
  }

  private establishConnection() {
    if (!this.callId || this.intentionalDisconnect) return;

    this.closeSocket();
    this.onStateChange(this.reconnectAttempts > 0 ? 'RECONNECTING' : 'CONNECTING');

    const wsUrl = `${CONFIG.WS_BASE_URL}/calls/${this.callId}/events`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.onStateChange('LIVE');
    };

    this.ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as WsEvent;
        if (event && event.type) {
          this.onEvent(event);
        }
      } catch (error) {
        console.warn('Malformed websocket event received', error);
      }
    };

    this.ws.onclose = () => {
      if (!this.intentionalDisconnect) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (e) => {
      console.warn('WebSocket error', e);
      // onclose will usually be called after this
    };
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.onStateChange('DISCONNECTED');
      return;
    }

    const backoffDelay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    
    this.onStateChange('RECONNECTING');

    this.reconnectTimeout = setTimeout(() => {
      this.establishConnection();
    }, backoffDelay);
  }

  private closeSocket() {
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.onmessage = null;
      this.ws.onopen = null;
      this.ws.close();
      this.ws = null;
    }
  }

  private handleAppStateChange(nextAppState: AppStateStatus) {
    if (nextAppState === 'background' || nextAppState === 'inactive') {
      // Gracefully close connection to save battery, will trigger onclose which schedules reconnect
      // But we don't want it reconnecting in the background aggressively
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }
      this.closeSocket();
      this.onStateChange('DISCONNECTED');
    } else if (nextAppState === 'active') {
      if (!this.intentionalDisconnect && this.callId && !this.ws) {
        // App woke up, re-establish
        this.reconnectAttempts = 0;
        this.establishConnection();
      }
    }
  }
}
