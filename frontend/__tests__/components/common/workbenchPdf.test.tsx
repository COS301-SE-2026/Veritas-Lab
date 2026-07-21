import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import type { Annotation, AnnotationPoint, AnnotationTool } from '@/types/workbench';
import WorkbenchPdf from '@/components/common/workbenchPdf';
import { pdfjs } from 'react-pdf';

const mockPageCount = 3;
const mockDocumentCalls: any[] = [];

jest.mock('react-pdf', () => {
    const ReactLib = require('react');

    const Document = (props: any) => {
        mockDocumentCalls.push(props);
        ReactLib.useEffect(() => {
            props.onLoadSuccess?.({ numPages: mockPageCount });
        }, []);
        return (
            <div data-testid="pdf-document" data-file={props.file}>
                {props.children}
            </div>
        );
    };

    const Page = ({ pageNumber, width, renderTextLayer, renderAnnotationLayer }: any) => (
        <div
            data-testid={`pdf-page-${pageNumber}`}
            data-width={width}
            data-render-text-layer={String(renderTextLayer)}
            data-render-annotation-layer={String(renderAnnotationLayer)}
        />
    );

    return {
        __esModule: true,
        Document,
        Page,
        pdfjs: {
            version: '4.0.0-test',
            GlobalWorkerOptions: { workerSrc: '' },
        },
    };
});

jest.mock('@/components/common/annotationLayer', () => ({
    __esModule: true,
    default: ({ page, active, activeTool, annotations, selectedId, onSelectAnnotation, onAddShape, onAddNote }: any) => (
        <div
            data-testid={`annotation-layer-${page}`}
            data-active={String(active)}
            data-active-tool={activeTool}
            data-selected-id={selectedId ?? ''}
            data-annotation-count={annotations.length}
        >
            <button onClick={() => onSelectAnnotation('picked-id')}>select-{page}</button>
            <button onClick={() => onAddShape([{ x: 1, y: 2 }], page)}>add-shape-{page}</button>
            <button onClick={() => onAddNote({ x: 3, y: 4 }, 'hello', page)}>add-note-{page}</button>
        </div>
    ),
}));


const mockAnnotations: Annotation[] = [{ id: 'a1' } as Annotation, { id: 'a2' } as Annotation];

const workbenchPdfProps = {
    url: 'https://example.com/file.pdf',
    mediaName: 'file.pdf',
    active: true,
    activeTool: 'Select' as AnnotationTool,
    annotations: mockAnnotations,
    selectedId: null as string | null,
    onSelectAnnotation: jest.fn(),
    onAddShape: jest.fn() as (points: AnnotationPoint[], page: number) => void,
    onAddNote: jest.fn() as (position: AnnotationPoint, text: string, page: number) => void,
};

function renderPdf(overrides: Partial<typeof workbenchPdfProps> = {}) {
    const props = { ...workbenchPdfProps, ...overrides };
    render(<WorkbenchPdf {...props} />);
    return props;
}

beforeEach(() => {
    jest.clearAllMocks();
    mockDocumentCalls.length = 0;
});

describe('WorkbenchPdf', () => {

    it('passes the file url to the document component', async () => {
        renderPdf({ url: 'https://example.com/report.pdf' });
        const doc = await screen.findByTestId('pdf-document');
        expect(doc).toHaveAttribute('data-file', 'https://example.com/report.pdf');
    });

    it('renders a page and AnnotationLayer for every page once loaded', async () => {
        renderPdf();
        for (let i = 1; i <= mockPageCount; i++) {
            expect(await screen.findByTestId(`pdf-page-${i}`)).toBeInTheDocument();
            expect(screen.getByTestId(`annotation-layer-${i}`)).toBeInTheDocument();
        }
    });

    it('forwards active, activeTool, annotations, and selectedId to each AnnotationLayer', async () => {
        renderPdf({ active: false, activeTool: 'Comment', selectedId: 'a2' });
        const layer = await screen.findByTestId('annotation-layer-1');
        expect(layer).toHaveAttribute('data-active', 'false');
        expect(layer).toHaveAttribute('data-active-tool', 'Comment');
        expect(layer).toHaveAttribute('data-selected-id', 'a2');
        expect(layer).toHaveAttribute('data-annotation-count', String(mockAnnotations.length));
    });

    it('propagates onSelectAnnotation from an AnnotationLayer', async () => {
        const props = renderPdf();
        await screen.findByTestId('annotation-layer-1');
        fireEvent.click(screen.getByText('select-1'));
        expect(props.onSelectAnnotation).toHaveBeenCalledWith('picked-id');
    });

    it('propagates onAddShape with points and page number', async () => {
        const props = renderPdf();
        await screen.findByTestId('annotation-layer-2');
        fireEvent.click(screen.getByText('add-shape-2'));
        expect(props.onAddShape).toHaveBeenCalledWith([{ x: 1, y: 2 }], 2);
    });

    it('propagates onAddNote with position, text, and page number', async () => {
        const props = renderPdf();
        await screen.findByTestId('annotation-layer-3');
        fireEvent.click(screen.getByText('add-note-3'));
        expect(props.onAddNote).toHaveBeenCalledWith({ x: 3, y: 4 }, 'hello', 3);
    });
});