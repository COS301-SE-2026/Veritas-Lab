const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

import type { AdminUser } from '@/types/api';

type ApiResult = {
    status?: 'success' | 'error';
    message?: string;
};

//get users list for cards.
export async function fetchUsers(): Promise<AdminUser[]> {
    const response = await fetch(`${API_BASE_URL}/api/fetchUsers`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
    });
    const data = (await response.json().catch(() => null)) as ApiResult & { users?: AdminUser[] } | AdminUser[] | null;
    if(!response.ok)
    {
        throw new Error((data && 'message' in data && data.message) || 'Failed to fetch users');
    }
    if(Array.isArray(data))
    {
        return data;
    }
    return data?.users ?? [];
}
//change role
export async function changeUserRole(userId: string, newRole: AdminUser['role']): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/changeUserRole`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId, NewRole: newRole }),
    });
    if(!response.ok)
    {
        const data = (await response.json().catch(() => null)) as ApiResult | null;
        throw new Error(data?.message || 'Failed to update user role');
    }
}
//del user
export async function deleteUser(userId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    if(!response.ok)
    {
        const data = (await response.json().catch(() => null)) as ApiResult | null;
        throw new Error(data?.message || 'Failed to delete user');
    }
}