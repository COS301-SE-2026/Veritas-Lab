import type { LoginResponse } from '@/types/api';

export async function login(email: string, password: string): Promise<LoginResponse> {
    const res = await fetch(`/api/login`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
    });

    const data: LoginResponse = await res.json();

    if (!res.ok) {
        throw new Error(data.message || 'Login failed');
    }

    return data;
}