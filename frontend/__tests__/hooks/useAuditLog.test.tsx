import { renderHook, waitFor } from '@testing-library/react';
import { getAllAudit } from '@/lib/api/audit';
import useAuditLog from '@/lib/hooks/useAuditLog';
jest.mock('@/lib/api/audit', () => ({
    getAllAudit: jest.fn(),
}));

describe('useAuditLog', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('fetches and returns audit log info', async () => {
        const mockedGetAllAudit = getAllAudit as jest.MockedFunction<typeof getAllAudit>;
        const mockedResponse = {
            status: 'success',
            cases: [
                {
                    caseId: 'case-1',
                    caseName: 'Alpha Fraud',
                    eventCount: 2,
                    lastEventTimestamp: '2026-05-02T10:30:00.000Z',
                    caseExists: true,
                },
                {
                    caseId: 'case-2',
                    caseName: 'Beta Theft',
                    eventCount: 1,
                    lastEventTimestamp: '2026-05-03T14:15:00.000Z',
                    caseExists: true,
                },
            ],
        };
        mockedGetAllAudit.mockResolvedValue(mockedResponse);

        const { result } = renderHook(() => useAuditLog());
        await waitFor(() => {
            expect(result.current.auditLogs).toEqual(mockedResponse);
        });
        expect(mockedGetAllAudit).toHaveBeenCalled();
        expect(result.current.isLoading).toBe(false);
        expect(result.current.error).toBeNull();
    });

    it('handles errors when fetching audit logs', async () => {
        const mockedGetAllAudit = getAllAudit as jest.MockedFunction<typeof getAllAudit>;
        mockedGetAllAudit.mockRejectedValue(new Error('Failed to load audit logs'));
        const { result } = renderHook(() => useAuditLog());
        await waitFor(() => {
            expect(result.current.error).toBe('Failed to load audit logs');
        });
        expect(result.current.auditLogs).toBeNull();
        expect(result.current.isLoading).toBe(false);
    });

});