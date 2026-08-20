import type { RegisterResponse } from '@/types/api';
import type { ApiError } from '@/types/api';

export async function register(username: string, email: string, password: string): Promise<RegisterResponse> {
    const res = await fetch(`/api/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password })
    });

    const data = await res.json();

    if (!res.ok) {
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Registration failed');
    }

    return data as RegisterResponse;
}
