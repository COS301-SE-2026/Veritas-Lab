import { fireEvent, render, screen, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import MetadataComparison from '@/components/common/workbenchMetadataComp';
jest.mock('@/lib/data/referenceMetadata', () => ({
    __esModule: true,
    referenceExamples: {
        image: [
            {
                id: 'image-a',
                label: 'Known bad example (image)',
                description: 'first image reference',
                data: { 'JUMBF:ActionsSoftwareAgentName': 'mock-agent' },
            },
            {
                id: 'image-b',
                label: 'Second image example',
                description: 'second image reference',
                data: { 'PNG:Software': 'ComfyUI' },
            },
        ],
        pdf: [
            {
                id: 'pdf-a',
                label: 'Known bad example (metadata stripped pdf)',
                description: 'pdf reference',
                data: { 'PDF:Producer': 'Mock Producer' },
            },
        ],
        video: [
            {
                id: 'video-a',
                label: 'Known bad example (video)',
                description: 'video reference',
                data: { 'JUMBF:ActionsSoftwareAgentName': 'mock-video-agent' },
            },
        ],
    },
}));

function getColumn(headingText: string): HTMLElement {
    return screen
        .getByRole('heading', { name: headingText, level: 4 })
        .closest('section') as HTMLElement;
}

const keysIn = (column: HTMLElement) =>
    Array.from(column.querySelectorAll('dt')).map(
        (element) => element.firstElementChild?.textContent ?? ''
    );

describe('MetadataComparison', () => {
    it('shows a fallback message for unsupported media kinds', () => {
        render(<MetadataComparison mediaKind="unsupported" mediaName="file.docx" />);
        expect(screen.getByText("Metadata comparison isnt available for this file type.")).toBeInTheDocument();
        expect(screen.queryByRole('heading', { name: 'Metadata comparison' })).not.toBeInTheDocument();
    });

    it('reads metadata out of the nested reportArtifacts.metadata field, not the envelope', () => {
        render(
            <MetadataComparison
                mediaKind="image"
                mediaName="evidence.png"
                reportArtifacts={{
                    bucket: 'images',
                    media_id: 'abc-123',
                    object_name: 'abc-123.png',
                    metadata: { 'File:FileName': 'abc-123.png' },
                }}
            />
        );
        const realColumn = getColumn('evidence.png');
        expect(within(realColumn).getByText('File:FileName')).toBeInTheDocument();
        expect(within(realColumn).queryByText('media_id')).not.toBeInTheDocument();
        expect(within(realColumn).queryByText('object_name')).not.toBeInTheDocument();
        expect(within(realColumn).queryByText('bucket')).not.toBeInTheDocument();
    });

    describe('reference examples', () => {
        it('renders the first image example on the right', () => {
            render(<MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={null} />);
            const exampleColumn = getColumn('Known bad example (image)');
            expect(within(exampleColumn).getByText('JUMBF:ActionsSoftwareAgentName')).toBeInTheDocument();
            expect(within(exampleColumn).getByText('mock-agent')).toBeInTheDocument();
        });

        it('renders the PDF example, not the image example', () => {
            render(<MetadataComparison mediaKind="pdf" mediaName="evidence.pdf" reportArtifacts={null} />);
            const exampleColumn = getColumn('Known bad example (metadata stripped pdf)');
            expect(within(exampleColumn).getByText('PDF:Producer')).toBeInTheDocument();
            expect(screen.queryByText('JUMBF:ActionsSoftwareAgentName')).not.toBeInTheDocument();
        });

        it('renders the video example, not the image or pdf example', () => {
            render(<MetadataComparison mediaKind="video" mediaName="evidence.mp4" reportArtifacts={null} />);
            const exampleColumn = getColumn('Known bad example (video)');
            expect(within(exampleColumn).getByText('mock-video-agent')).toBeInTheDocument();
            expect(screen.queryByText('PDF:Producer')).not.toBeInTheDocument();
        });

        it('cycles to the next example when the swap button is clicked', () => {
            render(<MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={null} />);
            expect(screen.getByRole('heading', { name: 'Known bad example (image)', level: 4 })).toBeInTheDocument();
            fireEvent.click(screen.getByRole('button', { name: /Swap example/ }));
            expect(screen.getByRole('heading', { name: 'Second image example', level: 4 })).toBeInTheDocument();
            expect(screen.getByText('ComfyUI')).toBeInTheDocument();
            expect(screen.queryByRole('heading', { name: 'Known bad example (image)', level: 4 })).not.toBeInTheDocument();
        });

        it('hides the swap button when a media kind only has one example', () => {
            render(<MetadataComparison mediaKind="pdf" mediaName="evidence.pdf" reportArtifacts={null} />);
            expect(screen.queryByRole('button', { name: /Swap example/ })).not.toBeInTheDocument();
        });
    });

    describe('value formatting', () => {
        it('shows a placeholder when there is no real metadata yet', () => {
            render(<MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={null} />);
            const realColumn = getColumn('evidence.png');
            expect(within(realColumn).getByText('No fields match the current filters.')).toBeInTheDocument();
        });

        it('marks empty metadata values as empty', () => {
            render(
                <MetadataComparison
                    mediaKind="image"
                    mediaName="evidence.png"
                    reportArtifacts={{ metadata: { 'EXIF:Make': '' } }}
                />
            );
            const realColumn = getColumn('evidence.png');
            expect(within(realColumn).getByText('EXIF:Make')).toBeInTheDocument();
            expect(within(realColumn).getByText('empty')).toBeInTheDocument();
        });

        it('hides empty values when the hide empty toggle is on', () => {
            render(
                <MetadataComparison
                    mediaKind="image"
                    mediaName="evidence.png"
                    reportArtifacts={{ metadata: { 'EXIF:Make': '', 'File:FileName': 'evidence.png' } }}
                />
            );
            fireEvent.click(screen.getByLabelText('Hide empty'));
            const realColumn = getColumn('evidence.png');
            expect(within(realColumn).queryByText('EXIF:Make')).not.toBeInTheDocument();
            expect(within(realColumn).getByText('File:FileName')).toBeInTheDocument();
        });

        it('joins array metadata values with commas', () => {
            render(
                <MetadataComparison
                    mediaKind="image"
                    mediaName="evidence.png"
                    reportArtifacts={{ metadata: { 'JUMBF:ActionsWhen': ['2026:05:07', '2026:05:07'] } }}
                />
            );
            const realColumn = getColumn('evidence.png');
            expect(within(realColumn).getByText('2026:05:07, 2026:05:07')).toBeInTheDocument();
        });
    });

    describe('highlighting', () => {
        it('flags a C2PA claim generator that names a generative tool', () => {
            render(
                <MetadataComparison
                    mediaKind="image"
                    mediaName="evidence.png"
                    reportArtifacts={{
                        metadata: {
                            'JUMBF:Claim_Generator_InfoName': 'OpenAI Media Service API',
                            'File:FileName': 'evidence.png',
                        },
                    }}
                />
            );
            const realColumn = getColumn('evidence.png');
            const flagged = within(realColumn)
                .getByText('JUMBF:Claim_Generator_InfoName')
                .closest('div') as HTMLElement;
            expect(within(flagged).getByText('AI')).toBeInTheDocument();
 
            const clean = within(realColumn).getByText('File:FileName').closest('div') as HTMLElement;
            expect(within(clean).queryByText('AI')).not.toBeInTheDocument();
        });

        it('flags diffusion parameters left in a PNG text chunk even without any C2PA data', () => {
            render(
                <MetadataComparison
                    mediaKind="image"
                    mediaName="evidence.png"
                    reportArtifacts={{
                        metadata: {
                            'PNG:Parameters': 'a cat Steps: 28, Sampler: DPM++ 2M, CFG scale: 7, Seed: 3841102934',
                        },
                    }}
                />
            );
            const realColumn = getColumn('evidence.png');
            const flagged = within(realColumn).getByText('PNG:Parameters').closest('div') as HTMLElement;
            expect(within(flagged).getByText('AI')).toBeInTheDocument();
        });

        it('flags editing software as an edit signal rather than an AI signal', () => {
            render(
                <MetadataComparison
                    mediaKind="image"
                    mediaName="evidence.png"
                    reportArtifacts={{ metadata: { 'EXIF:Software': 'Adobe Photoshop 26.2 (Windows)' } }}
                />
            );
            const realColumn = getColumn('evidence.png');
            const flagged = within(realColumn).getByText('EXIF:Software').closest('div') as HTMLElement;
            expect(within(flagged).getByText('Edited')).toBeInTheDocument();
            expect(within(flagged).queryByText('AI')).not.toBeInTheDocument();
        });

        it('reports missing capture fields as a file level insight', () => {
            render(
                <MetadataComparison
                    mediaKind="image"
                    mediaName="evidence.png"
                    reportArtifacts={{ metadata: { 'File:FileName': 'evidence.png' } }}
                />
            );
            expect(screen.getByText('No capture device recorded')).toBeInTheDocument();
            expect(screen.getByText('No original capture date')).toBeInTheDocument();
        });

        it('does not raise capture insights when the camera fields are present', () => {
            render(
                <MetadataComparison
                    mediaKind="image"
                    mediaName="evidence.png"
                    reportArtifacts={{
                        metadata: {
                            'EXIF:Make': 'Canon',
                            'EXIF:Model': 'Canon EOS 90D',
                            'EXIF:DateTimeOriginal': '2026:03:02 14:12:08',
                        },
                    }}
                />
            );
            expect(screen.queryByText('No capture device recorded')).not.toBeInTheDocument();
            expect(screen.queryByText('No original capture date')).not.toBeInTheDocument();
        });
    });

    describe('filtering', () => {
        const metadata = {
            'JUMBF:Claim_Generator_InfoName': 'gpt-image',
            'EXIF:Software': 'Adobe Photoshop 26.2 (Windows)',
            'File:FileName': 'evidence.png',
            'File:FileSize': '204800',
        };

        it('filters rows by a search term across keys and values', () => {
            render(
                <MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={{ metadata }} />
            );
            fireEvent.change(screen.getByLabelText('Filter metadata'), { target: { value: 'FileName' } });
            const realColumn = getColumn('evidence.png');
            expect(keysIn(realColumn)).toEqual(['File:FileName']);
        });

        it('searches values as well as keys', () => {
            render(
                <MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={{ metadata }} />
            );
            fireEvent.change(screen.getByLabelText('Filter metadata'), { target: { value: 'photoshop' } });
            const realColumn = getColumn('evidence.png');
            expect(keysIn(realColumn)).toEqual(['EXIF:Software']);
        });

        it('shows only flagged rows under the Flagged filter', () => {
            render(
                <MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={{ metadata }} />
            );
            fireEvent.click(screen.getByRole('button', { name: 'Flagged' }));
            const realColumn = getColumn('evidence.png');
            expect(keysIn(realColumn)).toEqual([
                'JUMBF:Claim_Generator_InfoName',
                'EXIF:Software',
            ]);
        });

        it('shows only AI rows under the AI filter', () => {
            render(
                <MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={{ metadata }} />
            );
            fireEvent.click(screen.getByRole('button', { name: 'AI' }));
            const realColumn = getColumn('evidence.png');
            expect(keysIn(realColumn)).toEqual(['JUMBF:Claim_Generator_InfoName']);
        });

        it('filters by metadata group', () => {
            render(
                <MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={{ metadata }} />
            );
            fireEvent.change(screen.getByLabelText('Filter by metadata group'), { target: { value: 'File' } });
            const realColumn = getColumn('evidence.png');
            expect(keysIn(realColumn)).toEqual(['File:FileName', 'File:FileSize']);
        });

        it('sorts flagged rows to the top by default and stops when the toggle is off', () => {
            render(
                <MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={{ metadata }} />
            );
            const realColumn = getColumn('evidence.png');
            expect(keysIn(realColumn)[0]).toBe('JUMBF:Claim_Generator_InfoName');
 
            fireEvent.click(screen.getByLabelText('Flagged first'));
            expect(keysIn(getColumn('evidence.png'))).toEqual(Object.keys(metadata));
        });
    });

    it('does not cap the number of displayed fields', () => {
        const metadata: Record<string, unknown> = {
            'JUMBF:Claim_Generator_InfoName': 'gpt-image',
        };
        for (let index = 0; index < 30; index += 1) {
            metadata[`File:Key${index}`] = `value-${index}`;
        }

        render(<MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={{ metadata }} />);
        const realColumn = getColumn('evidence.png');
        expect(realColumn.querySelectorAll('dt')).toHaveLength(31);
        expect(within(realColumn).getByText('File:Key29')).toBeInTheDocument();
    });
});