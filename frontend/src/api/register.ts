const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type RegisterResponse = {
    status: 'success' | 'error';
    message: string;
};

export async function register(name: string, email: string, password: string): Promise<RegisterResponse > {
    const res = await fetch(`${API_URL}/api/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, email, password })
    });
    
    const data: RegisterResponse = await res.json();

    if (!res.ok) {
        throw new Error(data.message || 'Registration failed');
    }

    return data;
}
