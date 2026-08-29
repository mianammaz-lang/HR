import { create } from 'zustand';

interface User {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  team?: string;
  is_active: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  hydrated: boolean;
  hydrate: () => void;
  login: (token: string, user: User) => void;
  logout: () => void;
  setUser: (user: User) => void;
}

// No default/bypass user — the app starts logged out. `hydrate()` restores
// a session from localStorage on the client after mount (SSR has no
// localStorage, so this can't run during server rendering).
export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  hydrated: false,

  hydrate: () => {
    if (typeof window === 'undefined') return;
    const token = localStorage.getItem('token');
    const userRaw = localStorage.getItem('user');
    if (token && userRaw) {
      try {
        const user = JSON.parse(userRaw) as User;
        set({ token, user, isAuthenticated: true, hydrated: true });
        return;
      } catch {
        // fall through to logged-out state
      }
    }
    set({ hydrated: true });
  },

  login: (token: string, user: User) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    set({ token, user, isAuthenticated: true, hydrated: true });
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({ token: null, user: null, isAuthenticated: false, hydrated: true });
  },

  setUser: (user: User) => {
    localStorage.setItem('user', JSON.stringify(user));
    set({ user });
  },
}));

interface AppState {
  sidebarOpen: boolean;
  activeView: 'dashboard' | 'database' | 'forms' | 'settings';
  toggleSidebar: () => void;
  setActiveView: (view: 'dashboard' | 'database' | 'forms' | 'settings') => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  activeView: 'dashboard',
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setActiveView: (view) => set({ activeView: view }),
}));
