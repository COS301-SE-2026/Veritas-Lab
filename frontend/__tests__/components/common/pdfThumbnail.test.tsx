import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import PdfThumbnail from '@/components/common/pdfThumbnail';

jest.mock('react-pdf', () => ({
    __esModule: true,
    pdfjs: { GlobalWorkerOptions: {}, version: 'test' },
    Document: ({ file, children }: any) => (
        <div data-testid="document" data-file={file}>{children}</div>
    ),
    Page: ({ pageNumber, width, renderTextLayer, renderAnnotationLayer }: any) => (
        <div
            data-testid="page"
            data-page-number={pageNumber}
            data-width={width}
            data-render-text-layer={String(renderTextLayer)}
            data-render-annotation-layer={String(renderAnnotationLayer)}
        />
    ),
}));

describe('PdfThumbnail', () => {
    it('renders the given PDF url in the Document', () => {
        render(<PdfThumbnail url="/evidence.pdf" />);
        expect(screen.getByTestId('document')).toHaveAttribute('data-file', '/evidence.pdf');
    });

    it('renders only the first page with text and annotation layers disabled', () => {
        render(<PdfThumbnail url="/evidence.pdf" />);
        const page = screen.getByTestId('page');
        expect(page).toHaveAttribute('data-page-number', '1');
        expect(page).toHaveAttribute('data-render-text-layer', 'false');
        expect(page).toHaveAttribute('data-render-annotation-layer', 'false');
    });

    it('uses a default width of 96 when none is provided', () => {
        render(<PdfThumbnail url="/evidence.pdf" />);
        expect(screen.getByTestId('page')).toHaveAttribute('data-width', '96');
    });

    it('applies a custom width when provided', () => {
        render(<PdfThumbnail url="/evidence.pdf" width={200} />);
        expect(screen.getByTestId('page')).toHaveAttribute('data-width', '200');
    });
});