import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import CasePage from '@/app/case-page/[id]/page';
import { fetchCase, addEvidence, closeCase, deleteEvidence, editComment, deleteComment, updateCase, addComment, } from '@/lib/api/case';
//only mocking backend api everything else needs to be real
jest.mock('@/lib/api/case', () => ({
    fetchCase: jest.fn(),
    addEvidence: jest.fn(),
    closeCase: jest.fn(),
    deleteEvidence: jest.fn(),
    editComment: jest.fn(),
    deleteComment: jest.fn(),
    updateCase: jest.fn(),
    addComment: jest.fn(),
}));
jest.mock('next/navigation', () => ({
    useParams: () => ({ id: 'case-1' }),
}));

const mockUseUserRole = jest.fn();
const mockUseCurrentUser = jest.fn();
jest.mock('@/context/UserRoleContext', () => ({
    useUserRole: () => mockUseUserRole(),
    useCurrentUser: () => mockUseCurrentUser(),
}));
jest.mock('next/image', () => ({
    __esModule: true,
    default: ({ src, alt }: { src: string; alt: string }) => <img src={src} alt={alt} />,
}));
jest.mock('next/link', () => ({
    __esModule: true,
    default: ({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) => (
        <a href={href} className={className}>{children}</a>
    ),
}));
jest.mock('next/dynamic', () => () => {
    const DynamicComponent = () => null;
    DynamicComponent.displayName = 'MockedDynamicComponent';
    return DynamicComponent;
});
jest.mock('@/lib/media', () => ({
    getMediaKind: (extension: string) => {
        if (extension === 'pdf') {
            return 'pdf';
        }
        if (['png', 'jpg', 'jpeg'].includes(extension)) {
            return 'image';
        }
        return 'other';
    },
}));

//data to be tested
const baseCase = {
    status: 'success',
    case: {
        caseId: 'case-1',
        caseName: 'Alpha Fraud',
        caseDescription: 'Suspicious transaction pattern',
        caseCreator: 'investigator.one',
        caseClosed: false,
        caseCreationDate: '2026-05-01T09:00:00.000Z',
    },
    evidence: [
        {
            reportId: 'report-1',
            mediaId: 'media-1',
            mediaName: 'Screenshot.png',
            mediaUrl: 'https://example.com/screenshot.png',
            mediaExtension: 'png',
        },
    ],
    comments: [
        {
            commentId: 1,
            caseId: 'case-1',
            username: 'investigator.one',
            comment: 'Initial review complete',
            timestamp: '2026-05-01T10:00:00.000Z',
        },
    ],
};

//tests for entire case page coming soon :(
describe('CasePage (integration)', () => {
    const mockedFetchCase = fetchCase as jest.MockedFunction<typeof fetchCase>;
    const mockedAddEvidence = addEvidence as jest.MockedFunction<typeof addEvidence>;
    const mockedCloseCase = closeCase as jest.MockedFunction<typeof closeCase>;
    const mockedDeleteEvidence = deleteEvidence as jest.MockedFunction<typeof deleteEvidence>;
    const mockedEditComment = editComment as jest.MockedFunction<typeof editComment>;
    const mockedDeleteComment = deleteComment as jest.MockedFunction<typeof deleteComment>;
    const mockedUpdateCase = updateCase as jest.MockedFunction<typeof updateCase>;
    const mockedAddComment = addComment as jest.MockedFunction<typeof addComment>;
    let toLocaleDateStringSpy: jest.SpyInstance;
    beforeEach(() => {
        jest.clearAllMocks();
        toLocaleDateStringSpy = jest.spyOn(Date.prototype, 'toLocaleDateString').mockReturnValue('01/05/2026');
        mockUseUserRole.mockReturnValue('INVESTIGATOR');
        mockUseCurrentUser.mockReturnValue({ username: 'investigator.one' });
        mockedFetchCase.mockResolvedValue(baseCase as Awaited<ReturnType<typeof fetchCase>>);
    });
    
    afterEach(() => {
        toLocaleDateStringSpy.mockRestore();
    });

    it('loads the case and shows full management controls for the owning investigator', async () => {
        render(<CasePage />);
        expect(screen.getByText('Loading case...')).toBeInTheDocument();
        expect(await screen.findByText('Alpha Fraud')).toBeInTheDocument();
        expect(screen.getByText('Suspicious transaction pattern')).toBeInTheDocument();
        expect(screen.getByText('Status: Open')).toBeInTheDocument();
        expect(screen.getByText('Created: 01/05/2026')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Edit Case' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Upload Evidence' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Close Case' })).toBeInTheDocument();
        expect(screen.getByText('Screenshot.png')).toBeInTheDocument();
        expect(screen.getByAltText('Screenshot.png')).toBeInTheDocument();
    }); 

    it('hides all management controls and the evidence delete button for normal user', async () => {
        mockUseUserRole.mockReturnValue('USER');
        render(<CasePage />);
        await screen.findByText('Alpha Fraud');
        expect(screen.queryByRole('button', { name: 'Edit Case' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Upload Evidence' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Close Case' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: '' })).not.toBeInTheDocument();
    });

    it('hides the edit button for an investigator who does not own the case but keeps upload/close', async () => {
        mockUseCurrentUser.mockReturnValue({ username: 'someone.else' });//potentially need to review this because permissions are weird
        render(<CasePage />);
        await screen.findByText('Alpha Fraud');
        expect(screen.queryByRole('button', { name: 'Edit Case' })).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Upload Evidence' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Close Case' })).toBeInTheDocument();
    });

    it('shows an error message when the case fails to load', async () => {
        mockedFetchCase.mockRejectedValue(new Error('Failed to load case'));
        render(<CasePage />);
        expect(await screen.findByText('Failed to load case')).toBeInTheDocument();
        expect(screen.getByText('Case not found')).toBeInTheDocument();
    });

    it('closes the case and reflects the closed status after reload', async () => {
        mockedCloseCase.mockResolvedValue({ status: 'success' });
        mockedFetchCase.mockResolvedValueOnce(baseCase as Awaited<ReturnType<typeof fetchCase>>);
        mockedFetchCase.mockResolvedValueOnce({
            ...baseCase,
            case: { ...baseCase.case, caseClosed: true },
        } as Awaited<ReturnType<typeof fetchCase>>);
        render(<CasePage />);
        await screen.findByText('Alpha Fraud');
        fireEvent.click(screen.getByRole('button', { name: 'Close Case' }));
        await waitFor(() => expect(mockedCloseCase).toHaveBeenCalledWith('case-1'));
        await waitFor(() => expect(screen.getByText('Status: Closed')).toBeInTheDocument());
        expect(screen.queryByRole('button', { name: 'Close Case' })).not.toBeInTheDocument();
        expect(mockedFetchCase).toHaveBeenCalledTimes(2);
    });

    it('edits the case name and description and reflects the change after reload', async () => {
        mockedUpdateCase.mockResolvedValue({ status: 'success' });
        mockedFetchCase.mockResolvedValueOnce(baseCase as Awaited<ReturnType<typeof fetchCase>>);
        mockedFetchCase.mockResolvedValueOnce({
            ...baseCase,
            case: { ...baseCase.case, caseName: 'Alpha Fraud (Updated)', caseDescription: 'Escalated' },
        } as Awaited<ReturnType<typeof fetchCase>>);
        render(<CasePage />);
        await screen.findByText('Alpha Fraud');
        fireEvent.click(screen.getByRole('button', { name: 'Edit Case' }));
        fireEvent.change(screen.getByDisplayValue('Alpha Fraud'), { target: { value: 'Alpha Fraud (Updated)' } });
        fireEvent.change(screen.getByDisplayValue('Suspicious transaction pattern'), { target: { value: 'Escalated' } });
        fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));
        await waitFor(() =>
            expect(mockedUpdateCase).toHaveBeenCalledWith('case-1', {
                caseName: 'Alpha Fraud (Updated)',
                caseDescription: 'Escalated',
            })
        );
        expect(await screen.findByText('Alpha Fraud (Updated)')).toBeInTheDocument();
        expect(screen.getByText('Escalated')).toBeInTheDocument();
    });

    it('uploads new piece of evidence and shows it after reload', async () => {
        mockedAddEvidence.mockResolvedValue({ status: 'success' });
        const updatedEvidence = [
            ...baseCase.evidence,
            {
                reportId: 'report-2',
                mediaId: 'media-2',
                mediaName: 'newfile.png',
                mediaUrl: 'https://example.com/newfile.png',
                mediaExtension: 'png',
            },
        ];
        mockedFetchCase.mockResolvedValueOnce(baseCase as Awaited<ReturnType<typeof fetchCase>>);
        mockedFetchCase.mockResolvedValueOnce({
            ...baseCase,
            evidence: updatedEvidence,
        } as Awaited<ReturnType<typeof fetchCase>>);
        render(<CasePage />);
        await screen.findByText('Alpha Fraud');
        fireEvent.click(screen.getByRole('button', { name: 'Upload Evidence' }));
        const file = new File(['dummy'], 'newfile.png', { type: 'image/png' });
        fireEvent.change(screen.getByLabelText('Upload Media'), { target: { files: [file] } });
        fireEvent.click(screen.getByRole('button', { name: 'Upload Media' }));
        await waitFor(() => expect(mockedAddEvidence).toHaveBeenCalledWith(file, 'case-1'));
        expect(await screen.findByText('newfile.png')).toBeInTheDocument();
        expect(mockedFetchCase).toHaveBeenCalledTimes(2);
    });

    it('deletes evidence and removes it from the list after reload', async () => {
        mockedDeleteEvidence.mockResolvedValue({ status: 'success' });
        mockedFetchCase.mockResolvedValueOnce(baseCase as Awaited<ReturnType<typeof fetchCase>>);
        mockedFetchCase.mockResolvedValueOnce({
            ...baseCase,
            evidence: [],
        } as Awaited<ReturnType<typeof fetchCase>>);
        render(<CasePage />);
        await screen.findByText('Screenshot.png');
        fireEvent.click(screen.getByRole('button', { name: '' }));
        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
        await waitFor(() => expect(mockedDeleteEvidence).toHaveBeenCalledWith('case-1', 'media-1'));
        await waitFor(() => expect(screen.queryByText('Screenshot.png')).not.toBeInTheDocument());
        expect(screen.getByText('No evidence uploaded yet.')).toBeInTheDocument();
    });

    it('switches to the Comments tab and submits a new comment', async () => {
        mockedAddComment.mockResolvedValue({
            commentId: 2,
            caseId: 'case-1',
            username: 'investigator.one',
            comment: 'Following up with the bank',
            timestamp: '2026-05-02T09:00:00.000Z',
        });
        render(<CasePage />);
        await screen.findByText('Alpha Fraud');
        fireEvent.click(screen.getByRole('button', { name: 'Comments' }));
        expect(await screen.findByText('Initial review complete')).toBeInTheDocument();
        fireEvent.change(screen.getByPlaceholderText('Write your comment here'), {
            target: { value: 'Following up with the bank' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Send Comment' }));
        await waitFor(() => expect(mockedAddComment).toHaveBeenCalledWith('case-1', 'Following up with the bank'));
        expect(await screen.findByText('Following up with the bank')).toBeInTheDocument();
        expect(mockedFetchCase).toHaveBeenCalledTimes(1);
    });

    it('edits an existing comment from the Comments tab', async () => {
        mockedEditComment.mockResolvedValue({ status: 'success' });
        render(<CasePage />);
        await screen.findByText('Alpha Fraud');
        fireEvent.click(screen.getByRole('button', { name: 'Comments' }));
        await screen.findByText('Initial review complete');
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        fireEvent.change(screen.getByDisplayValue('Initial review complete'), {
            target: { value: 'Initial review complete - escalated' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
        await waitFor(() =>
            expect(mockedEditComment).toHaveBeenCalledWith('case-1', 1, 'Initial review complete - escalated')
        );
        expect(await screen.findByText('Initial review complete - escalated')).toBeInTheDocument();
    });
});