import type { ApiError } from "@/types/api";
import type { CaseBoard } from "@/types/components";
import { apiFetch } from "./client";

export type CaseBoardResponse = {
    caseBoard: CaseBoard;
};

export async function getCaseBoard(caseId: string): Promise<CaseBoard | null> {
    const res = await apiFetch(`/api/CaseBoard/${caseId}`, {
        method: 'GET',
    });

    const data = await res.json().catch(() => null);
    if (!res.ok) {
        const error = data as ApiError | null;
        throw new Error(error?.detail?.message || 'Failed to load case board');
    }

    return (data as CaseBoardResponse | null)?.caseBoard ?? null;
}

export async function saveCaseBoard(caseId: string, caseBoard: CaseBoard, options?: { keepalive?: boolean }): Promise<void> {
    const res = await apiFetch(`/api/saveCaseBoard/${caseId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ caseId, caseBoard }),
        keepalive: options?.keepalive
    });

    const data = await res.json().catch(() => null);
    if (!res.ok) {
        const error = data as ApiError | null;
        throw new Error(error?.detail?.message || 'Failed to save case board');
    }
}