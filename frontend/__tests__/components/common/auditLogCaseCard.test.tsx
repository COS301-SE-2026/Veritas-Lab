import { fireEvent, render, screen } from '@testing-library/react';
import AuditLogCaseCard from '@/components/common/auditLogCaseCard';
import { AuditLogCase } from '@/types/api';
jest.mock('lucide-react', () => ({
    __esModule: true,
    ChevronDown: jest.fn(() => <div data-testid="chevron-icon">ChevronDown Icon</div>),
}));

describe('AuditLogCaseCard', () => {
    const mockedCase: AuditLogCase = {
        caseId: 'case-1',
        caseName: 'Case 1',
        eventCount: 2,
        lastEventTimestamp: '2026-09-11T11:30:00.000Z',
        caseExists: true,
    };
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('renders case ID in closed state', () => {
        render(<AuditLogCaseCard cases={mockedCase}  />);
        expect(screen.getByText('case-1')).toBeInTheDocument();
        expect(screen.queryByText('Case Name: Case 1')).not.toBeInTheDocument();
        expect(screen.queryByText('Events: 2')).not.toBeInTheDocument();
        expect(screen.queryByText('Last Event: 2026-09-11T11:30:00.000Z')).not.toBeInTheDocument();
        expect(screen.queryByText('Exists: true')).not.toBeInTheDocument();
    });

    it('renders case ID and events in open state', () => {
        render(<AuditLogCaseCard cases={mockedCase} />);
        const chevy = screen.getByTestId('chevron-icon');
        fireEvent.click(chevy);

        expect(screen.getByText('case-1')).toBeInTheDocument();
        expect(screen.getByText('Case ID: case-1')).toBeInTheDocument();
        expect(screen.getByText('Case Name: Case 1')).toBeInTheDocument();
        expect(screen.getByText('Events: 2')).toBeInTheDocument();
        expect(screen.getByText('Last Event: 2026-09-11T11:30:00.000Z')).toBeInTheDocument();
        expect(screen.getByText('Exists: true')).toBeInTheDocument();
    });

    it('collapses events when clicking the chevron icon again', () => {
        render(<AuditLogCaseCard cases={mockedCase} />);
        const chevy = screen.getByTestId('chevron-icon');
        fireEvent.click(chevy);
        expect(screen.getByText('Case ID: case-1')).toBeInTheDocument();
        expect(screen.getByText('Case Name: Case 1')).toBeInTheDocument();
        expect(screen.getByText('Events: 2')).toBeInTheDocument();
        expect(screen.getByText('Last Event: 2026-09-11T11:30:00.000Z')).toBeInTheDocument();
        expect(screen.getByText('Exists: true')).toBeInTheDocument();
        fireEvent.click(chevy);
        expect(screen.queryByText('Case ID: case-1')).not.toBeInTheDocument();
        expect(screen.queryByText('Case Name: Case 1')).not.toBeInTheDocument();
        expect(screen.queryByText('Events: 2')).not.toBeInTheDocument();
        expect(screen.queryByText('Last Event: 2026-09-11T11:30:00.000Z')).not.toBeInTheDocument();
        expect(screen.queryByText('Exists: true')).not.toBeInTheDocument();
    });
})