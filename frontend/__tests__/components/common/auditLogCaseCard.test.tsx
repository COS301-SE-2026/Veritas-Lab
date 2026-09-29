import { fireEvent, render, screen } from '@testing-library/react';
import AuditLogCaseCard from '@/components/common/auditLogCaseCard';
import { AuditEvents, AuditLogCase } from '@/types/api';
jest.mock('lucide-react', () => ({
    __esModule: true,
    ChevronDown: jest.fn(() => <div data-testid="chevron-icon">ChevronDown Icon</div>),
}));

describe('AuditLogCaseCard', () => {
    const mockedCase: AuditLogCase = {
        caseId: 'case-1',
        caseName: 'Case 1',
        eventCount: 1,
        lastEventTimestamp: '2026-09-11T11:30:00.000Z',
        caseExists: true,
        events: [
            {
                
                timestamp: '2026-09-11T11:30:00.000Z',
                user: 'user1',
                action: 'Created case',
            }
        ]
    };
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('renders case ID in closed state', () => {
        render(<AuditLogCaseCard caseLog={mockedCase}/>);
        expect(screen.getByText('Case 1')).toBeInTheDocument();
        expect(screen.queryByText('Case Name: Case 1')).not.toBeInTheDocument();
        expect(screen.queryByText('Events: 2')).not.toBeInTheDocument();
        expect(screen.queryByText('Last Event: 2026-09-11T11:30:00.000Z')).not.toBeInTheDocument();
        expect(screen.queryByText('Exists: true')).not.toBeInTheDocument();
    });

    it('renders case ID and events in open state', () => {
        render(<AuditLogCaseCard caseLog={mockedCase} />);
        fireEvent.click(screen.getByRole('button'));
        expect(screen.getByText('CaseId:')).toBeInTheDocument();
        expect(screen.getByText('case-1')).toBeInTheDocument();
        expect(screen.getByText('Event Count:')).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText('Last Event:')).toBeInTheDocument();
        expect(screen.getAllByText(new Date(mockedCase.lastEventTimestamp).toLocaleString()).length).toBeGreaterThan(0);
        expect(screen.getByText('user1')).toBeInTheDocument();
        expect(screen.getByText('Created case')).toBeInTheDocument();
    });

    it('collapses events when clicking the chevron icon again', () => {
        render(<AuditLogCaseCard caseLog={mockedCase} />);
        const button = screen.getByRole('button');
        fireEvent.click(button)
        expect(screen.getByText('case-1')).toBeInTheDocument();
        expect(screen.getByText('user1')).toBeInTheDocument();
        fireEvent.click(button);
        expect(screen.queryByText('CaseId')).not.toBeInTheDocument();
        expect(screen.queryByText('case-1')).not.toBeInTheDocument();
        expect(screen.queryByText('user1')).not.toBeInTheDocument()
        expect(screen.queryByText('Created case')).not.toBeInTheDocument();
    });
})