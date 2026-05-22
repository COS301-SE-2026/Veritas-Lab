'use client';
import { createContext, useCallback, useContext, useMemo, useState } from 'react';

type AuthContextType = {
    token: string | null;
    setToken: (token: string | null) => void;
};

const AuthContext = createContext<AuthContextType>({ token: null, setToken: () => {} });

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [token, setTokenState] = useState<string | null>(() => {
        if (typeof window === 'undefined') return null;

        return localStorage.getItem('authToken');
    });

    const setToken = useCallback((token: string | null) => {
        if (token) {
            localStorage.setItem('authToken', token);
        } else {
            localStorage.removeItem('authToken');
        }
        setTokenState(token);
    }, []);

    const value = useMemo(() => ({ token, setToken }), [token, setToken]);

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);