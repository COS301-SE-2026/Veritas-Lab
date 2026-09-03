import type { ApiError, ChangePasswordResponse } from '@/types/api';
//frontend call to backend
export async function changePassword(currentPassword: string, newPassword: string): Promise<ChangePasswordResponse> {
    const res = await fetch(`/api/changePassword`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ currentPassword, newPassword })
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
        const error = data as ApiError | null
        throw new Error(error?.detail?.message || 'Unable to change password');
    }
    return data as ChangePasswordResponse;
}