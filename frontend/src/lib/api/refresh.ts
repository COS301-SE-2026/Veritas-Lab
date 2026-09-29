
export async function refreshSession(): Promise<boolean> {
    try {
        const res = await fetch('/api/refresh', {
            method: 'POST',
            credentials: 'include',
        });
        return res.ok;
    } catch {
        return false;
    }
}