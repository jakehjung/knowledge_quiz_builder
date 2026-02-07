import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { userApi } from '@/services/api';
import type { ThemePreference } from '@/types';

interface ThemeContextType {
  theme: ThemePreference;
  setTheme: (theme: ThemePreference) => Promise<void>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, updateUser } = useAuth();
  const [theme, setThemeState] = useState<ThemePreference>('byu');

  useEffect(() => {
    // Reset to default theme when logged out, use user preference when logged in
    setThemeState(user?.theme_preference ?? 'byu');
  }, [user]);

  useEffect(() => {
    document.documentElement.classList.remove('theme-byu', 'theme-utah');
    document.documentElement.classList.add(`theme-${theme}`);
  }, [theme]);

  const setTheme = async (newTheme: ThemePreference) => {
    setThemeState(newTheme);
    if (isAuthenticated) {
      try {
        const updatedUser = await userApi.updateProfile({ theme_preference: newTheme });
        updateUser(updatedUser);
      } catch (error) {
        console.error('Failed to save theme preference:', error);
      }
    }
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
