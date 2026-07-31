import type { RegisterResponse } from '@/types/api';

export async function register(username: string, email: string, password: string): Promise<RegisterResponse> {
    const res = await fetch(`/api/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password })
    });

    const data: RegisterResponse = await res.json();

    if (!res.ok) {
        throw new Error(data.message || 'Registration failed');
    }

    return data;
}
