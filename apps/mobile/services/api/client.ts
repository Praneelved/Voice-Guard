import { CONFIG } from '../../constants/config';
import { useAuthStore } from '../../stores/useAuthStore';

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export const apiClient = {
  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, headers, ...restOptions } = options;
    
    let url = `${CONFIG.API_BASE_URL}${endpoint}`;
    
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        searchParams.append(key, String(value));
      });
      url += `?${searchParams.toString()}`;
    }

    const token = useAuthStore.getState().token;
    
    const defaultHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        headers: {
          ...defaultHeaders,
          ...headers,
        },
        ...restOptions,
      });

      if (!response.ok) {
        throw new ApiError(response.status, `HTTP error! status: ${response.status}`);
      }

      return (await response.json()) as T;
    } catch (error) {
      console.error(`[API Client] Error calling ${url}:`, error);
      if (error instanceof ApiError) {
        throw error;
      }
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  },

  get<T>(endpoint: string, options?: RequestOptions) {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  },

  post<T>(endpoint: string, data?: any, options?: RequestOptions) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  patch<T>(endpoint: string, data?: any, options?: RequestOptions) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  },
  
  delete<T>(endpoint: string, options?: RequestOptions) {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  },
};
