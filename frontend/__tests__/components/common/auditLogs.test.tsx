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

        expect(screen.getByText('Loading audit logs...')).toBeInTheDocument();
        expect(useAuditLogMock).toHaveBeenCalled();
        expect(screen.queryByTestId('audit-log-case-card')).not.toBeInTheDocument();
    });
});