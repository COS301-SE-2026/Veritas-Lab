import { render, screen } from '@testing-library/react';
import useAuditLog from '@/lib/hooks/useAuditLog';
import AuditLogs from '@/components/common/auditLogs';
jest.mock('@/lib/hooks/useAuditLog', () => ({
    __esModule: true,
    default: jest.fn(),
}));

jest.mock('@/components/common/auditLogCaseCard', () => ({
    __esModule: true,
    default: jest.fn(({ cases }) => (
        <div data-testid="audit-log-case-card">
            <div data-testid="case-id">{cases.caseId}</div>
            <div data-testid="case-name">{cases.caseName}</div>
            <div data-testid="case-event-count">{cases.eventCount}</div>
            <div data-testid="case-last-event-timestamp">{cases.lastEventTimestamp}</div>
            <div data-testid="case-exists">{cases.caseExists.toString()}</div>
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
        const useAuditLogMock = useAuditLog as jest.Mock;
        const mockAuditLogs =  {
                status: 'success',
                cases: [
                    {
                        caseId: 'case-1',
                        caseName: 'Case 1',
                        eventCount: 2,
                        lastEventTimestamp: '2026-09-11T11:30:00.000Z',
                        caseExists: true,
                    },
                    {
                        caseId: 'case-2',
                        caseName: 'Case 2',
                        eventCount: 3,
                        lastEventTimestamp: '2026-09-11T12:30:00.000Z',
                        caseExists: false,
                    }
                ]
            } 
        const mockedResponse = {
            isLoading: false,
            error: null,
            auditLogs: mockAuditLogs
        };
        useAuditLogMock.mockReturnValue(mockedResponse);

        render(<AuditLogs />);
        expect(screen.queryByText('Loading audit logs...')).not.toBeInTheDocument();
        expect(screen.queryByTestId('error-label')).not.toBeInTheDocument();
        expect(screen.getAllByTestId('audit-log-case-card')).toHaveLength(2);

        expect(screen.getByText('case-1')).toBeInTheDocument();
        expect(screen.getByText('Case 1')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('2026-09-11T11:30:00.000Z')).toBeInTheDocument();
        expect(screen.getByText('true')).toBeInTheDocument();

        expect(screen.getByText('case-2')).toBeInTheDocument();
        expect(screen.getByText('Case 2')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
        expect(screen.getByText('2026-09-11T12:30:00.000Z')).toBeInTheDocument();
        expect(screen.getByText('false')).toBeInTheDocument();
    });
});