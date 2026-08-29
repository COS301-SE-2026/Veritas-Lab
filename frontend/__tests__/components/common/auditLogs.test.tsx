import { render, screen } from '@testing-library/react';
import useAuditLog from '@/lib/hooks/useAuditLog';
import AuditLogs from '@/components/common/auditLogs';
jest.mock('@/lib/hooks/useAuditLog', () => ({
    __esModule: true,
    default: jest.fn(),
}));

jest.mock('@/components/common/auditLogCaseCard', () => ({
    __esModule: true,
    default: jest.fn(({ caseId, events }) => (
        <div data-testid="audit-log-case-card">
            <div data-testid="case-id">{caseId}</div>
            <div data-testid="events">{JSON.stringify(events)}</div>
        </div>
    )),
}));

jest.mock('@/components/ui/label', () => ({
    __esModule: true,
    default: jest.fn(({ text }) => <div data-testid="error-label">{text}</div>),
}));

describe('AuditLogs', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders loading state', () => {
        const useAuditLogMock = useAuditLog as jest.Mock;
        const mockedResponse = {
            data: null,
            isLoading: true,
            error: null,
        }
        useAuditLogMock.mockReturnValue(mockedResponse);

        render(<AuditLogs />);

        expect(screen.queryByText('Loading audit logs...')).toBeInTheDocument();
        expect(useAuditLogMock).toHaveBeenCalled();
        expect(screen.queryByTestId('audit-log-case-card')).not.toBeInTheDocument();
    });

    it('renders audit logs when data is available', () => {
        // This test also is waiting fot the mock data to be removed so it can test properly
        const useAuditLogMock = useAuditLog as jest.Mock;
        const mockedResponse = {
            isLoading: false,
            error: null,
            auditLogs: [
                {
                    caseID: 'case-1',
                    events: [
                        {
                            timestamp: '2026-05-01T05:00:00.000Z',
                            action: 'Created case',
                            user: 'Invest Admin',
                        },
                        {
                            timestamp: '2026-05-02T10:30:00.000Z',
                            action: 'Added evidence',
                            user: 'Invest Admin',
                        }
                    ]
                },
                {
                    caseID: 'case-2',
                    events: [
                        {
                            timestamp: '2026-05-03T14:15:00.000Z',
                            action: 'Closed case',
                            user: 'Invest Admin',
                        }
                    ]
                }
            ]
        };
        useAuditLogMock.mockReturnValue(mockedResponse);

        render(<AuditLogs />);
        expect(screen.queryByText('Loading audit logs...')).not.toBeInTheDocument();
    });
});