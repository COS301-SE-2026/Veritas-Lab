'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
    const { token } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!token) router.replace('/login');
    }, [token, router]);

    if (!token) return null;

    return <>{children}</>;
}