import { render, screen } from '@testing-library/react';
import useAuditTimeline from '@/lib/hooks/useAuditTimeline';
import AuditTimeline from '@/components/common/auditTimeline';
jest.mock('@/lib/hooks/useAuditTimeline', () => ({
    __esModule: true,
    default: jest.fn(),
}));

jest.mock('@/components/ui/label', () => ({
    __esModule: true,
    default: jest.fn(({ text }) => <div data-testid="error-label">{text}</div>),
}));

jest.mock('lucide-react', () => ({
    __esModule: true,
    FolderPlus: jest.fn(() => <div>FolderPlus Icon</div>),
}));

describe('AuditTimeline', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders loading state', () => {
        const auditTimelineMock = useAuditTimeline as jest.Mock;
        const mockedResponse = {
            timeline: null,
            isLoading: true,
            error: null,
        };
        auditTimelineMock.mockReturnValue(mockedResponse);

        render(<AuditTimeline caseId="case-1" />);
        expect(screen.getByText('Loading timeline...')).toBeInTheDocument();
        expect(auditTimelineMock).toHaveBeenCalledWith('case-1');
    });

    it('renders error state', () => {
        const auditTimelineMock = useAuditTimeline as jest.Mock;
        const mockedResponse = {
            timeline: null,
            isLoading: false,
            error: 'Failed to load audit timeline',
        };
        auditTimelineMock.mockReturnValue(mockedResponse);

        render(<AuditTimeline caseId="case-1" />);
        const errorLabel = screen.getByTestId('error-label');
        expect(errorLabel).toBeInTheDocument();
        expect(errorLabel).toHaveTextContent('Failed to load audit timeline');
        expect(auditTimelineMock).toHaveBeenCalledWith('case-1');
    });
})