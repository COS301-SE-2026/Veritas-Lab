import type { DashboardCase } from '@/types/api';

export async function fetchCases(): Promise<DashboardCase[]> {
	try {
		const res = await fetch(`/api/getCases`, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({})
		});

		if (!res.ok) {
			throw new Error('Failed to fetch dashboard cases');
		}

		const data = await res.json();
		const serverCases = Array.isArray(data) ? data : data.cases ?? [];
		return serverCases as DashboardCase[];
	} catch (error) {
		console.error('Error fetching dashboard cases:', error);
		throw error;
	}
}

export async function createCase(title: string, description?: string): Promise<{ CaseId: string }> {
	try {
		const res = await fetch(`/api/createCase`, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ title, description }),
		});

		if (!res.ok) {
			const err = await res.json().catch(() => null);
			throw new Error(err?.message || 'Failed to create case');
		}

		const data = await res.json();
		return { CaseId: data.CaseId };
	} catch (error) {
		console.error('Error creating case:', error);
		throw error;
	}
}

export async function deleteCase(caseId: string): Promise<{ status: string; message?: string }> {
    try {
        const res = await fetch(`/api/deleteCase`, {
            method: 'DELETE',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ CaseID: caseId }),
        });
        const data = await res.json().catch(() => null);
        if (!res.ok) {
            throw new Error(data?.message ?? 'Failed to delete case');
        }
        return data;
    } catch (error) {
        console.error('Error deleting case:', error);
        throw error;
    }
}