import type { DashboardCase } from '@/types/api';
import type { ApiError } from '@/types/api';
export async function fetchCases(): Promise<DashboardCase[]> {
	const res = await fetch(`/api/getCases`, {
		method: 'POST',
		credentials: 'include',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({})
	});
	
	const data = await res.json().catch(() => null);
	if (!res.ok) {
		const error = data as ApiError | null
		throw new Error(error?.detail?.message || 'Failed to fetch dashboard cases');
	}

	const serverCases = Array.isArray(data) ? data : data.cases ?? [];
	return serverCases as DashboardCase[];
}

export async function createCase(title: string, description?: string): Promise<{ CaseId: string }> {
	const res = await fetch(`/api/createCase`, {
		method: 'POST',
		credentials: 'include',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({ title, description }),
	});

	const data = await res.json().catch(() => null);
	if (!res.ok) {
		const error = data as ApiError | null
		throw new Error(error?.detail?.message ||  'Failed to create case');
	}

	return { CaseId: data.CaseId };
}

export async function deleteCase(caseId: string): Promise<{ status: string; message?: string }> {
	const res = await fetch(`/api/deleteCase`, {
		method: 'DELETE',
		credentials: 'include',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ CaseID: caseId }),
	});
	const data = await res.json().catch(() => null);
	if (!res.ok) {
		const error = data as ApiError | null
		throw new Error(error?.detail?.message || 'Failed to delete case');
	}
	return data;
}