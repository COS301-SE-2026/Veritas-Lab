import { renderHook, waitFor } from '@testing-library/react';
import { getAllAudit } from '@/lib/api/audit';
import useAuditLog from '@/lib/hooks/useAuditLog';
import { AuditLogResponse } from '@/types/api';
jest.mock('@/lib/api/audit', () => ({
    getAllAudit: jest.fn(),
}));

describe('useAuditLog', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('fetches and returns audit log info', async () => {
        const mockedGetAllAudit = getAllAudit as jest.MockedFunction<typeof getAllAudit>;
        const mockedResponse: AuditLogResponse  = {
            auditLogs: [
                {
                    caseID: 'case-1',
                    events: [
                        {
                            timestamp: '2026-09-11T11:30:00.000Z',
                            user: 'user1',
                            action: 'Created case',
                        },
                        {
                            timestamp: '2026-09-11T11:30:00.000Z',
                            user: 'user1',
                            action: 'Created case',
                        }
                    ]
                },
                {
                    caseID: 'case-2',
                    events: [
                        {
                            timestamp: '2026-09-11T11:30:00.000Z',
                            user: 'user2',
                            action: 'Created case',
                        },
                        {
                            timestamp: '2026-09-11T11:30:00.000Z',
                            user: 'user1',
                            action: 'Created case',
                        }
                    ]
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