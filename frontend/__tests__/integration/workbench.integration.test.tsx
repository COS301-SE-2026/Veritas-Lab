import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import WorkbenchPage from '@/app/(sidebar)/case-page/[id]/workbench/[evidenceId]/page';
import { fetchCase } from '@/lib/api/case';
import { saveAnnotations } from '@/lib/api/workbench';
import type { CaseEvidence, CaseResponse } from '@/types/api';
jest.mock('@/lib/api/case', () => ({
    fetchCase: jest.fn(),
}));
jest.mock('@/lib/api/workbench', () => ({
    saveAnnotations: jest.fn(),
}));
jest.mock('next/navigation', () => ({
    useParams: () => ({ id: 'case-1', evidenceId: 'report-1' }),
}));
jest.mock('next/link', () => ({
    __esModule: true,
    default: ({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) => (
        <a href={href} className={className}>{children}</a>
    ),
}));
jest.mock('@/lib/media', () => ({
    getMediaKind: (extension?: string) => {
        if (extension === 'pdf') return 'pdf';
        if (extension && ['png', 'jpg', 'jpeg'].includes(extension)) return 'image';
        return 'unsupported';
    },
}));
jest.mock('@/lib/report', () => ({
    getCertaintyMeta: (certainty: number | null) => {
        const map: Record<number, { label: string; description: string; colorVar: string }> = {
            0: { label: 'Authentic', description: 'No signs of manipulation detected.', colorVar: 'green' },
            1: { label: 'Uncertain', description: 'Insufficient evidence to determine authenticity.', colorVar: 'gray' },
            2: { label: 'Suspicious', description: 'Some indicators of possible manipulation.', colorVar: 'orange' },
            3: { label: 'Manipulated', description: 'Strong evidence of manipulation.', colorVar: 'red' },
        };
        return certainty !== null && map[certainty] ? map[certainty] : { label: 'Unknown', description: 'Certainty not yet assessed.', colorVar: 'gray' };
    },
}));
jest.mock('next/dynamic', () => () => {
    const DynamicComponent = () => null;
    DynamicComponent.displayName = 'MockedDynamicComponent';
    return DynamicComponent;
});
const evidenceFixture: CaseEvidence = {
    reportId: 'report-1',
    mediaId: 'media-1',
    mediaName: 'Suspicious Screenshot.png',
    mediaBucket: 'bucket-1',
    mediaExtension: 'png',
    mediaTypeId: 'type-1',
    mediaUrl: 'https://example.com/screenshot.png',
    annotations: [
        { id: 'ann-1', kind: 'note', page: 1, position: { x: 50, y: 50 }, text: 'Pre-existing note' },
    ],
    reportArtifacts: {
        metadata: {
            'EXIF:CameraModel': 'Canon EOS 90D',
            'File:FileSize': '204800',
        },
    },
    reportFindings: 'Signs of AI generation detected.',
    reportCertainty: 2,
    reportComments: null,
    reportDateCreation: '2026-05-01T09:00:00.000Z',
};
const caseFixture: CaseResponse = {
    status: 'success',
    case: {
        caseId: 'case-1',
        caseName: 'Alpha Fraud',
        caseCreator: 'investigator.one',
        caseReviews: null,
        caseDescription: null,
        caseClosed: false,
        caseCreationDate: '2026-05-01T09:00:00.000Z',
    },
    comments: [],
    evidence: [evidenceFixture],
};
//tests now
describe('WorkbenchPage (integration)', () => {
    const mockedFetchCase = fetchCase as jest.MockedFunction<typeof fetchCase>;
    const mockedSaveAnnotations = saveAnnotations as jest.MockedFunction<typeof saveAnnotations>;
    beforeEach(() => {
        jest.resetAllMocks();
        mockedFetchCase.mockResolvedValue(caseFixture);
    });
    const openAnnotationsTool = async () => {
        await screen.findByAltText('Suspicious Screenshot.png');
        fireEvent.click(screen.getByRole('button', { name: 'Annotations' }));
    };
    //annotation etsts
    it('loads the matching evidence and shows the media with no annotation controls until a tool is picked', async () => {
        render(<WorkbenchPage />);
        expect(await screen.findByRole('heading', { name: 'Suspicious Screenshot.png' })).toBeInTheDocument();
        expect(screen.getByAltText('Suspicious Screenshot.png')).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /Back to case/i })).toHaveAttribute('href', '/case-page/case-1');
        expect(screen.getByRole('button', { name: 'Annotations' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'View side by side' })).toBeInTheDocument();
        expect(screen.queryByText('Click an annotation to view its details.')).not.toBeInTheDocument();
    });
    it('shows pre loaded annotations from the fetched evidence once the Annotations tool is active', async () => {
        render(<WorkbenchPage />);
        await openAnnotationsTool();
        expect(screen.getByText('Click an annotation to view its details.')).toBeInTheDocument();
        expect(screen.getByText('Pre-existing note')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /^Save$/ })).not.toBeDisabled();
    });
    it('draws a new shape annotation with the Draw tool', async () => {
        render(<WorkbenchPage />);
        await openAnnotationsTool();
        fireEvent.click(screen.getByRole('button', { name: 'Draw' }));
        const overlay = screen.getByRole('button', { name: 'Annotation layer, page 1' });
        fireEvent.pointerDown(overlay, { pointerId: 1, isPrimary: true, clientX: 10, clientY: 10 });
        fireEvent.pointerMove(overlay, { pointerId: 1, isPrimary: true, clientX: 20, clientY: 20 });
        fireEvent.pointerUp(overlay, { pointerId: 1, isPrimary: true, clientX: 20, clientY: 20 });
        const annotationsSection = screen.getByRole('heading', { name: 'Annotations' }).closest('div') as HTMLElement;
        expect(await within(annotationsSection).findByText('Circled region 2')).toBeInTheDocument();
    });
    //comments testing
    it('adds a new note with the Comment tool', async () => {
        render(<WorkbenchPage />);
        await openAnnotationsTool();
        fireEvent.click(screen.getByRole('button', { name: 'Comment' }));
        const overlay = screen.getByRole('button', { name: 'Annotation layer, page 1' });
        fireEvent.click(overlay);
        const draftTextarea = await screen.findByPlaceholderText('Why did you flag this?');
        fireEvent.change(draftTextarea, { target: { value: 'Follow up with the lab' } });
        fireEvent.click(screen.getByRole('button', { name: 'Save note' }));
        const annotationsSection = screen.getByRole('heading', { name: 'Annotations' }).closest('div') as HTMLElement;
        expect(await within(annotationsSection).findByText('Follow up with the lab')).toBeInTheDocument();
        expect(screen.queryByPlaceholderText('Why did you flag this?')).not.toBeInTheDocument();
    });
    it('removes an annotation', async () => {
        render(<WorkbenchPage />);
        await openAnnotationsTool();
        await screen.findByText('Pre-existing note');
        fireEvent.click(screen.getByRole('button', { name: 'Remove annotation' }));
        expect(screen.queryByText('Pre-existing note')).not.toBeInTheDocument();
        expect(screen.getByText('No annotations yet. Use the Draw or Comment tool on the media.')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /^Save$/ })).toBeDisabled();
    });
    it('saves annotations successfully', async () => {
        mockedSaveAnnotations.mockResolvedValue(undefined);
        render(<WorkbenchPage />);
        await openAnnotationsTool();
        fireEvent.click(screen.getByRole('button', { name: /^Save$/ }));
        await waitFor(() =>
            expect(mockedSaveAnnotations).toHaveBeenCalledWith({
                evidenceId: 'report-1',
                annotations: evidenceFixture.annotations,
            })
        );
        expect(await screen.findByText('Annotations saved successfully!')).toBeInTheDocument();
    });
    it('shows an error when saving annotations fails', async () => {
        mockedSaveAnnotations.mockRejectedValue(new Error('Failed to save annotations'));
        render(<WorkbenchPage />);
        await openAnnotationsTool();
        fireEvent.click(screen.getByRole('button', { name: /^Save$/ }));
        expect(await screen.findByText('Failed to save annotations')).toBeInTheDocument();
    });
    it('clears all annotations', async () => {
        render(<WorkbenchPage />);
        await openAnnotationsTool();
        await screen.findByText('Pre-existing note');
        fireEvent.click(screen.getByRole('button', { name: /^Clear$/ }));
        expect(screen.queryByText('Pre-existing note')).not.toBeInTheDocument();
        expect(screen.getByText('No annotations yet. Use the Draw or Comment tool on the media.')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /^Clear$/ })).toBeDisabled();
    });
    //side by side
    it('shows the side by side metadata comparison', async () => {
        render(<WorkbenchPage />);
        await screen.findByAltText('Suspicious Screenshot.png');
        fireEvent.click(screen.getByRole('button', { name: 'View side by side' }));
        expect(screen.getByText('Metadata side-by-side')).toBeInTheDocument();
        expect(screen.getByText('EXIF:CameraModel')).toBeInTheDocument();
        expect(screen.getByText('Canon EOS 90D')).toBeInTheDocument();
        expect(screen.getByText('Known bad example (image)')).toBeInTheDocument();
        expect(screen.getByText('JUMBF:ActionsSoftwareAgentName')).toBeInTheDocument();
        expect(screen.getByText('gpt-image')).toBeInTheDocument();
    });
    //report
    it('opens and closes the report modal with the evidence details', async () => {
        render(<WorkbenchPage />);
        await screen.findByAltText('Suspicious Screenshot.png');
        fireEvent.click(screen.getByRole('button', { name: /Show Report/i }));
        expect(screen.getByRole('heading', { name: 'Report' })).toBeInTheDocument();
        expect(screen.getByText('Suspicious')).toBeInTheDocument();
        expect(screen.getByText('Some indicators of possible manipulation.')).toBeInTheDocument();
        expect(screen.getByText('Signs of AI generation detected.')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Close report' }));
        expect(screen.queryByRole('heading', { name: 'Report' })).not.toBeInTheDocument();
    });
    //error loading
    it('falls back to a generic title and empty preview when the case fails to load', async () => {
        mockedFetchCase.mockRejectedValue(new Error('Failed to load evidence media'));
        render(<WorkbenchPage />);
        expect(await screen.findByRole('heading', { name: 'Evidence report-1' })).toBeInTheDocument();
        expect(screen.getByText('No media preview available yet')).toBeInTheDocument();
    });
    it('falls back to a generic title when the case loads but has no matching evidence', async () => {
        mockedFetchCase.mockResolvedValue({ ...caseFixture, evidence: [] });
        render(<WorkbenchPage />);
        expect(await screen.findByRole('heading', { name: 'Evidence report-1' })).toBeInTheDocument();
        expect(screen.getByText('No media preview available yet')).toBeInTheDocument();
    });
});