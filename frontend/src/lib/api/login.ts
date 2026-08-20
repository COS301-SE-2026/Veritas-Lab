import type { LoginResponse } from '@/types/api';
import type { ApiError } from '@/types/api';
export async function login(email: string, password: string): Promise<LoginResponse> {
    const res = await fetch(`/api/login`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (!res.ok) {
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Login failed');
    }

    return data as LoginResponse;
}