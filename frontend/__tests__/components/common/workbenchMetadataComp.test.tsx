import { render, screen, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import MetadataComparison from '@/components/common/workbenchMetadataComp';

jest.mock('lucide-react', () => ({
    __esModule: true,
    Columns2: () => <div data-testid="columns-icon" />,
}));

jest.mock('@/lib/data/referenceMetadata', () => ({
    __esModule: true,
    badExampleData: {
        image: { 'JUMBF:ActionsSoftwareAgentName': 'mock-agent' },
        pdf: { 'PDF:Producer': 'Mock Producer' },
    },
    exampleLabels: {
        image: 'Known bad example (image)',
        pdf: 'Known bad example (PDF)',
    },
}));

function getColumn(headingText: string): HTMLElement {
    return screen
        .getByRole('heading', { name: headingText, level: 4 })
        .closest('div') as HTMLElement;
}

describe('MetadataComparison', () => {
    it('shows a fallback message for unsupported media kinds', () => {
        render(<MetadataComparison mediaKind="unsupported" mediaName="file.docx" />);
        expect(
            screen.getByText("Metadata comparison isnt available for this file type.")
        ).toBeInTheDocument();
        expect(screen.queryByText('Metadata comparison')).not.toBeInTheDocument();
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

    it('renders the static example metadata on the right for an image', () => {
        render(<MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={null} />);
        expect(screen.getByText('Known bad example (image)')).toBeInTheDocument();
        expect(screen.getByText('JUMBF:ActionsSoftwareAgentName')).toBeInTheDocument();
        expect(screen.getByText('mock-agent')).toBeInTheDocument();
    });

    it('renders the static example metadata for a PDF, not the image example', () => {
        render(<MetadataComparison mediaKind="pdf" mediaName="evidence.pdf" reportArtifacts={null} />);
        expect(screen.getByText('Known bad example (PDF)')).toBeInTheDocument();
        expect(screen.getByText('PDF:Producer')).toBeInTheDocument();
        expect(screen.queryByText('JUMBF:ActionsSoftwareAgentName')).not.toBeInTheDocument();
    });

    it('shows a placeholder when there is no real metadata yet', () => {
        render(<MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={null} />);
        expect(screen.getAllByText('No metadata available.').length).toBeGreaterThan(0);
    });

    it('renders an underscore for empty or missing metadata values', () => {
        render(
            <MetadataComparison
                mediaKind="image"
                mediaName="evidence.png"
                reportArtifacts={{ metadata: { 'EXIF:Make': '' } }}
            />
        );
        expect(screen.getByText('EXIF:Make')).toBeInTheDocument();
        expect(screen.getByText('_')).toBeInTheDocument();
    });

    it('joins array metadata values with commas', () => {
        render(
            <MetadataComparison
                mediaKind="image"
                mediaName="evidence.png"
                reportArtifacts={{ metadata: { 'JUMBF:ActionsWhen': ['2026:05:07', '2026:05:07'] } }}
            />
        );
        expect(screen.getByText('2026:05:07, 2026:05:07')).toBeInTheDocument();
    });

    describe('PNG metadata extraction', () => {
        it('shows all metadata unfiltered when there is no agent/claim-generator signal', () => {
            render(
                <MetadataComparison
                    mediaKind="image"
                    mediaName="evidence.png"
                    reportArtifacts={{
                        metadata: {
                            'JUMBF:Hash': '(Binary data 32 bytes, use -b option to extract)',
                            'File:FileName': 'evidence.png',
                        },
                    }}
                />
            );
            const realColumn = getColumn('evidence.png');
            expect(within(realColumn).getByText('JUMBF:Hash')).toBeInTheDocument();
            expect(within(realColumn).getByText('File:FileName')).toBeInTheDocument();
        });

        it('surfaces agent/claim-generator JUMBF keys first and drops other JUMBF noise', () => {
            render(
                <MetadataComparison
                    mediaKind="image"
                    mediaName="evidence.png"
                    reportArtifacts={{
                        metadata: {
                            'JUMBF:Hash': '(Binary data 32 bytes, use -b option to extract)',
                            'JUMBF:ActionsWhen': '2026:05:07',
                            'File:FileName': 'evidence.png',
                            'JUMBF:ActionsSoftwareAgentName': 'gpt-image',
                            'JUMBF:Claim_Generator_InfoName': 'OpenAI Media Service API',
                        },
                    }}
                />
            );
            const realColumn = getColumn('evidence.png');
            expect(within(realColumn).getByText('JUMBF:ActionsSoftwareAgentName')).toBeInTheDocument();
            expect(within(realColumn).getByText('JUMBF:Claim_Generator_InfoName')).toBeInTheDocument();
            expect(within(realColumn).getByText('File:FileName')).toBeInTheDocument();
            expect(within(realColumn).queryByText('JUMBF:Hash')).not.toBeInTheDocument();
            expect(within(realColumn).queryByText('JUMBF:ActionsWhen')).not.toBeInTheDocument();
            const keyOrder = Array.from(realColumn.querySelectorAll('dt')).map((el) => el.textContent);
            expect(keyOrder.indexOf('JUMBF:ActionsSoftwareAgentName')).toBeLessThan(
                keyOrder.indexOf('File:FileName')
            );
        });

        it('caps the displayed entries at 25 once a flag is raised', () => {
            const metadata: Record<string, unknown> = {
                'JUMBF:Claim_Generator_InfoName': 'gpt-image',
            };
            for (let i = 0; i < 30; i += 1) {
                metadata[`File:Key${i}`] = `value-${i}`;
            }

            render(<MetadataComparison mediaKind="image" mediaName="evidence.png" reportArtifacts={{ metadata }} />);
            const realColumn = getColumn('evidence.png');
            expect(realColumn.querySelectorAll('dt')).toHaveLength(25);
            expect(within(realColumn).getByText('JUMBF:Claim_Generator_InfoName')).toBeInTheDocument();
            expect(within(realColumn).getByText('File:Key0')).toBeInTheDocument();
            expect(within(realColumn).queryByText('File:Key29')).not.toBeInTheDocument();
        });

        it('does not cap or filter metadata for PDFs', () => {
            const metadata: Record<string, unknown> = {};
            for (let i = 0; i < 30; i += 1) {
                metadata[`PDF:Key${i}`] = `value-${i}`;
            }
            render(<MetadataComparison mediaKind="pdf" mediaName="evidence.pdf" reportArtifacts={{ metadata }} />);
            const realColumn = getColumn('evidence.pdf');
            expect(realColumn.querySelectorAll('dt')).toHaveLength(30);
        });
    });
});