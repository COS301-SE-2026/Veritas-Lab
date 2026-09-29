import { deleteCookie } from '@/auth/cookie';

export async function apiFetch(input: RequestInfo, init?: RequestInit) {
    const res = await fetch(input, {credentials: 'include', ...init});
    if (res.status === 401) {
        await deleteCookie();
        if (typeof window !== 'undefined') {
            window.location.href = '/login';
        }
        throw new Error('Session expired. Log in again.');
    }
    return res;
}