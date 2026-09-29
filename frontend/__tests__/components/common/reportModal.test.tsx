import { render, screen, fireEvent } from '@testing-library/react';
import ReportModal from '@/components/common/reportModal';

jest.mock('@/components/ui/modal', () => ({
    __esModule: true,
    default: ({ isOpen, children }: { isOpen: boolean; children: React.ReactNode }) =>
        isOpen ? <div data-testid="modal">{children}</div> : null,
}));

jest.mock('@/lib/report', () => ({
    getCertaintyMeta: jest.fn((certainty: number | null) => ({
        colorVar: `var(--certainty-${certainty})`,
        label: `Label-${certainty}`,
        description: `Description for certainty ${certainty}`,
    })),
}));

jest.mock('lucide-react', () => ({
    __esModule: true,
    X: (props: Record<string, unknown>) => <svg data-testid="icon-x" {...props} />,
    ShieldCheck: (props: Record<string, unknown>) => <svg data-testid="icon-shield-check" {...props} />,
    ShieldQuestion: (props: Record<string, unknown>) => <svg data-testid="icon-shield-question" {...props} />,
    ShieldAlert: (props: Record<string, unknown>) => <svg data-testid="icon-shield-alert" {...props} />,
    ShieldX: (props: Record<string, unknown>) => <svg data-testid="icon-shield-x" {...props} />,
}));

const baseProps = {
    isOpen: true,
    onClose: jest.fn(),
    mediaUrl: '/evidence-a.png',
    mediaKind: 'image' as const,
    mediaName: 'EvidenceA',
    certainty: 1,
    findings: { risk_level: 1, findings: 'Some findings text' },
};
//alot of these tests are similar to existing workbench tests but need to be repeated for this component
describe('ReportModal', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('does not render when isOpen is false', () => {
        render(<ReportModal {...baseProps} isOpen={false} />);
        expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
    });

    it('renders the media name', () => {
        render(<ReportModal {...baseProps} />);
        expect(screen.getByText('EvidenceA')).toBeInTheDocument();
    });

    it('calls onClose when the close button is clicked', () => {
        const onClose = jest.fn();
        render(<ReportModal {...baseProps} onClose={onClose} />);
        fireEvent.click(screen.getByRole('button', { name: 'Close report' }));
        expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('renders reasons for images', () => {
        render(<ReportModal {...baseProps} mediaKind="image" />);
        expect(screen.getByText('REASONS')).toBeInTheDocument();
    })

    it('renders reasons for pdfs', () => {
        render(<ReportModal {...baseProps} mediaKind="pdf" mediaUrl="/evidence-a.pdf" />);
        expect(screen.getByText('REASONS')).toBeInTheDocument();
    })

    it('renders reasons for unsupported media types', () => {
        render(<ReportModal {...baseProps} mediaKind="unsupported" mediaUrl="/evidence-a.txt" />);
        expect(screen.queryByText('REASONS')).not.toBeInTheDocument();
    });

    it('renders the certainty label and description from getCertaintyMeta', () => {
        render(<ReportModal {...baseProps} certainty={2} />);
        expect(screen.getByText('Label-2')).toBeInTheDocument();
        expect(screen.getByText('Description for certainty 2')).toBeInTheDocument();
    });
    //lucide icon render test
    it.each([
        [0, 'icon-shield-check'],
        [1, 'icon-shield-question'],
        [2, 'icon-shield-alert'],
        [3, 'icon-shield-x'],
    ])('renders the mapped icon for certainty %i', (certainty, testId) => {
        render(<ReportModal {...baseProps} certainty={certainty} />);
        expect(screen.getByTestId(testId)).toBeInTheDocument();
    });

    it('falls back to the question icon when certainty is null', () => {
        render(<ReportModal {...baseProps} certainty={null} />);
        expect(screen.getByTestId('icon-shield-question')).toBeInTheDocument();
    });

    it('falls back to the question icon for an unmapped certainty value', () => {
        render(<ReportModal {...baseProps} certainty={99} />);
        expect(screen.getByTestId('icon-shield-question')).toBeInTheDocument();
    });

    it('renders findings text when provided', () => {
        render(<ReportModal {...baseProps} findings={{ risk_level: 2, findings: 'Detected manipulation in metadata' }} />);
        expect(screen.getByText('Detected manipulation in metadata')).toBeInTheDocument();
    });

    it('renders fallback message when findings is null', () => {
        render(<ReportModal {...baseProps} findings={null} />);
        expect(screen.getByText('No reasons available yet for this evidence.')).toBeInTheDocument();
    });
});