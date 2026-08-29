import { render, screen } from '@testing-library/react';
import AuditLogCaseCard from '@/components/common/auditLogCaseCard';
import { AuditEvents } from '@/types/api';
jest.mock('lucide-react', () => ({
    __esModule: true,
    ChevronDown: jest.fn(() => <div data-testid="chevron-icon">ChevronDown Icon</div>),
    FolderPlus: jest.fn(() => <div data-testid="folder-plus-icon">FolderPlus Icon</div>),
}));

describe('AuditLogCaseCard', () => {
    const mockedCaseId = 'case-1';
    const mockedEvents: AuditEvents[] = [
            {
                timestamp: '2026-05-01T05:00:00.000Z',
                action: 'Created case',
                user: 'Invest Admin',
            },
            {
                timestamp: '2026-05-02T10:30:00.000Z',
                action: 'Added evidence',
                user: 'Invest Admin',
            },
        ];
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('renders case ID in closed state', () => {
        render(<AuditLogCaseCard caseId={mockedCaseId} events={mockedEvents} />);
        expect(screen.getByText(mockedCaseId)).toBeInTheDocument();
        expect(screen.queryByText('Created case')).not.toBeInTheDocument();
        expect(screen.queryByText('Added evidence')).not.toBeInTheDocument();
    })

})