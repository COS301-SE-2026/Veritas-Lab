const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

import { getAuthHeaders } from './authHeaders';

type LoginResponse = {
    status: 'success' | 'error';
    token: string;
    message?: string;
};

export async function login(email: string, password: string): Promise<LoginResponse> {
    const res = await fetch(`${API_URL}/api/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        },
        body: JSON.stringify({ email, password })
    });

    const data: LoginResponse = await res.json();

    if (!res.ok) {
        throw new Error(data.message || 'Login failed');
    }

    return data;
}