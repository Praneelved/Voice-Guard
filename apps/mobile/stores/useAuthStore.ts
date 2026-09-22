import { create } from 'zustand';
import { supabase } from '../services/supabase';
import { Session } from '@supabase/supabase-js';
import { User } from '../types';

interface AuthState {
  user: User | null;
  session: Session | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setSession: (session: Session | null) => void;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  session: null,
  token: null,
  isAuthenticated: false,
  isLoading: true, // Start loading until session is checked
  
  setSession: (session: Session | null) => {
    if (session) {
      set({
        session,
        token: session.access_token,
        user: {
          id: session.user.id,
          email: session.user.email || '',
          name: session.user.user_metadata?.name || 'User',
        },
        isAuthenticated: true,
        isLoading: false,
      });
    } else {
      set({
        session: null,
        token: null,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },
  
  logout: async () => {
    await supabase.auth.signOut();
    set({ user: null, session: null, token: null, isAuthenticated: false });
  },
}));

// Set up the listener outside the store to hydrate immediately
supabase.auth.getSession().then(({ data: { session } }) => {
  useAuthStore.getState().setSession(session);
});

supabase.auth.onAuthStateChange((_event, session) => {
  useAuthStore.getState().setSession(session);
});
