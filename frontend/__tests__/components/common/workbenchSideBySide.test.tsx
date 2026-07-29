import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MetadataComparison from '@/components/common/workbenchSideBySide';

jest.mock('lucide-react', () => ({
    __esModule: true,
    Columns2: () => <div data-testid="columns-icon" />,
}));

jest.mock('@/lib/data/referenceMetadata', () => ({
    __esModule: true,
    EXAMPLE_BAD_METADATA: {
        image: { 'EXIF:Software': 'Mock Editor 1.0' },
        pdf: { 'PDF:Producer': 'Mock Producer' },
    },
    EXAMPLE_METADATA_LABELS: {
        image: 'Known bad example (image)',
        pdf: 'Known bad example (PDF)',
    },
}));

describe('MetadataComparison', () => {
    it('shows a fallback message for unsupported media kinds', () => {
        render(<MetadataComparison mediaKind="unsupported" mediaName="file.docx" />);
        expect(
            screen.getByText("Metadata comparison isnt available for this file type.")
        ).toBeInTheDocument();
        expect(screen.queryByText('Metadata side-by-side')).not.toBeInTheDocument();
    });

    it('renders the real file metadata on the left for an image', () => {
        render(
            <MetadataComparison
                mediaKind="image"
                mediaName="evidence.jpg"
                metadata={{ 'EXIF:Model': 'Pixel 8' }}
            />
        );
        expect(screen.getByText('evidence.jpg')).toBeInTheDocument();
        expect(screen.getByText('EXIF:Model')).toBeInTheDocument();
        expect(screen.getByText('Pixel 8')).toBeInTheDocument();
    });

    it('renders the static example metadata on the right for an image', () => {
        render(<MetadataComparison mediaKind="image" mediaName="evidence.jpg" metadata={{}} />);
        expect(screen.getByText('Known bad example (image)')).toBeInTheDocument();
        expect(screen.getByText('EXIF:Software')).toBeInTheDocument();
        expect(screen.getByText('Mock Editor 1.0')).toBeInTheDocument();
    });

    it('renders the static example metadata for a PDF, not the image example', () => {
        render(<MetadataComparison mediaKind="pdf" mediaName="evidence.pdf" metadata={{}} />);
        expect(screen.getByText('Known bad example (PDF)')).toBeInTheDocument();
        expect(screen.getByText('PDF:Producer')).toBeInTheDocument();
        expect(screen.queryByText('EXIF:Software')).not.toBeInTheDocument();
    });

    it('shows a placeholder when there is no real metadata yet', () => {
        render(<MetadataComparison mediaKind="image" mediaName="evidence.jpg" metadata={null} />);
        expect(screen.getAllByText('No metadata available.').length).toBeGreaterThan(0);
    });

    it('renders an underscore for empty or missing metadata values', () => {
        render(
            <MetadataComparison
                mediaKind="image"
                mediaName="evidence.jpg"
                metadata={{ 'EXIF:Make': '' }}
            />
        );
        expect(screen.getByText('EXIF:Make')).toBeInTheDocument();
        expect(screen.getByText('_')).toBeInTheDocument();
    });

    it('joins array metadata values with commas', () => {
        render(
            <MetadataComparison
                mediaKind="image"
                mediaName="evidence.jpg"
                metadata={{ 'JFIF:JFIFVersion': [1, 1] }}
            />
        );
        expect(screen.getByText('1, 1')).toBeInTheDocument();
    });
});