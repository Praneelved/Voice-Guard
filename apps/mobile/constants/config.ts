export const CONFIG = {
  API_BASE_URL: process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/v1',
  WS_BASE_URL: process.env.EXPO_PUBLIC_WS_URL || 'ws://localhost:8000/v1',
  APP_ENV: process.env.EXPO_PUBLIC_APP_ENV || 'development',
  USE_MOCKS: process.env.EXPO_PUBLIC_USE_MOCKS === 'true',
};
