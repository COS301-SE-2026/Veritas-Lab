export function getAuthHeaders(): Record<string, string> {
    if (typeof window === 'undefined') {
        return {};
    }

    const token = window.localStorage.getItem('authToken');

    if (!token) {
        return {};
    }

    return {
        Authorization: `Bearer ${token}`,
    };
}