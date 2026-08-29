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
            auditLogs: [
                {
                    caseID: 'case-1',
                    events: [
                        {
                            timestamp: '2026-05-01T05:00:00.000Z',
                            user: 'Invest Admin',
                            action: 'Created case',
                        },
                        {
                            timestamp: '2026-05-02T10:30:00.000Z',
                            user: 'Invest Admin',
                            action: 'Added evidence',
                        }
                    ]
                },
                {
                    caseID: 'case-2',
                    events: [
                        {
                            timestamp: '2026-05-03T14:15:00.000Z',
                            user: 'Invest Admin',
                            action: 'Closed case',
                        }
                    ]
                }
            ]
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

});