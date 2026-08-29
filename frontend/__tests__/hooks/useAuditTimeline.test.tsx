import { renderHook, waitFor } from '@testing-library/react';
import { getAudit } from "@/lib/api/audit";
import useAuditTimeline from '@/lib/hooks/useAuditTimeline';

jest.mock('@/lib/api/audit', () => ({
    getAudit: jest.fn(),
}));

describe('useAuditTimeline', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('fetches and returns audit timeline data', async () => {
        const caseId = 'case-1';
        const mockedGetAudit = getAudit as jest.MockedFunction<typeof getAudit>;
        const mockedResponse = {
            caseID: 'case-1',
            events: [
                {
                    action: 'Created case',
                    user: 'Invest Admin',
                    timestamp: '2026-05-01T05:00:00.000Z',
                },
            ],
        }
        mockedGetAudit.mockResolvedValue(mockedResponse);

        const { result } = renderHook(() => useAuditTimeline(caseId));
        await waitFor(() => {
            expect(result.current.timeline).toEqual(mockedResponse);
        });
        expect(mockedGetAudit).toHaveBeenCalledWith(caseId);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.error).toBeNull();
    });

    it('handles errors when fetching audit timeline', async () => {
        const caseId = 'case-2';
        const mockedGetAudit = getAudit as jest.MockedFunction<typeof getAudit>;
        mockedGetAudit.mockRejectedValue(new Error('Failed to load audit timeline'));
        const { result } = renderHook(() => useAuditTimeline(caseId));
        await waitFor(() => {
            expect(result.current.error).toBe('Failed to load audit timeline');
        });
        expect(result.current.timeline).toBeUndefined();
        expect(result.current.isLoading).toBe(false);
    });
});