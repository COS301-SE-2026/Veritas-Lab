const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

import { getAuthHeaders } from './authHeaders';
import type { RegisterResponse } from '@/types/api';

export async function register(username: string, email: string, password: string): Promise<RegisterResponse > {
    const res = await fetch(`${API_URL}/api/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        },
        body: JSON.stringify({ username, email, password })
    });
    
    const data: RegisterResponse = await res.json();

    if (!res.ok) {
        throw new Error(data.message || 'Registration failed');
    }

    return data;
}
