import type { AdminUser, ApiError } from '@/types/api';
import { apiFetch } from './client';
type ApiResult = {
    status?: 'success' | 'error';
    message?: string;
};

//get users list for cards.
export async function fetchUsers(): Promise<AdminUser[]> {
    const response = await apiFetch(`/api/fetchUsers`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
    });

    const data = (await response.json().catch(() => null)) as ApiResult & { users?: AdminUser[] } | AdminUser[] | null;
    if(!response.ok) {
        const error = data as ApiError | null
        throw new Error(error?.detail.message || 'Failed to fetch users')
    }
    if (Array.isArray(data)) {
        return data;
    }
    return data?.users ?? [];
}

//change role
export async function changeUserRole(userId: string, newRole: AdminUser['role']): Promise<void> {
    const response = await apiFetch(`/api/changeUserRole`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId, NewRole: newRole }),
    });
    if(!response.ok) {
        const error = (await response.json().catch(() => null)) as ApiError | null
        throw new Error(error?.detail.message || 'Failed to update user role')
    }
}
//del user
export async function deleteUser(userId: string): Promise<void> {
    const response = await apiFetch(`/api/users/${userId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    if (!response.ok) {
        const error = (await response.json().catch(() => null)) as ApiError | null;
        throw new Error(error?.detail.message || 'Failed to delete user');
    }
}