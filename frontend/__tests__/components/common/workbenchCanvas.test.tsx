import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import type { AnnotationTool, WorkbenchCanvasProps } from '@/types/workbench';
import WorkbenchCanvas from '@/components/common/workbenchCanvas';

jest.mock('next/dynamic', () => ({
    __esModule: true,
    default: () => {
        const MockWorkbenchPdf = (props: any) => (
            <div data-testid="workbench-pdf-mock" data-props={JSON.stringify(props)} />
        );
        MockWorkbenchPdf.displayName = 'MockWorkbenchPdf';
        return MockWorkbenchPdf;
    },
}));

jest.mock('lucide-react', () => ({
    __esModule: true,
    ImageOff: (props: any) => <svg data-testid="icon-image-off" {...props} />,
}));

jest.mock('@/components/common/annotationLayer', () => ({
    __esModule: true,
    default: (props: any) => <div data-testid={`annotation-layer-${props.page}`} data-props={JSON.stringify(props)} />,
}));

const workbenchCanvasProps: WorkbenchCanvasProps = {
    mediaUrl: null,
    mediaKind: 'unsupported',
    mediaName: 'evidence.file',
    active: true,
    activeTool: 'Select' as AnnotationTool,
    annotations: [],
    selectedId: null,
    onSelectAnnotation: jest.fn(),
    onAddShape: jest.fn(),
    onAddNote: jest.fn(),
};

function renderCanvas(overrides: Partial<WorkbenchCanvasProps> = {}) {
    const props = { ...workbenchCanvasProps, ...overrides };
    render(<WorkbenchCanvas {...props} />);
    return props;
}

beforeEach(() => {
    jest.clearAllMocks();
});

describe('WorkbenchCanvas', () => {
    describe('image media', () => {
        it('renders the image with the correct src and alt text', () => {
            renderCanvas({ mediaUrl: 'https://example.com/pic.png', mediaKind: 'image', mediaName: 'pic.png' });
            const img = screen.getByRole('img', { name: 'pic.png' });
            expect(img).toHaveAttribute('src', 'https://example.com/pic.png');
        });

        it('disables pointer events on the image when active', () => {
            renderCanvas({ mediaUrl: 'https://example.com/pic.png', mediaKind: 'image', active: true });
            expect(screen.getByRole('img')).toHaveClass('pointer-events-none');
        });

        it('allows pointer events on the image when not active', () => {
            renderCanvas({ mediaUrl: 'https://example.com/pic.png', mediaKind: 'image', active: false });
            expect(screen.getByRole('img')).not.toHaveClass('pointer-events-none');
        });

        it('renders an AnnotationLayer for page 1 with the layer props', () => {
            const props = renderCanvas({
                mediaUrl: 'https://example.com/pic.png',
                mediaKind: 'image',
                activeTool: 'Draw',
                selectedId: 'a1',
            });
            const layer = screen.getByTestId('annotation-layer-1');
            const forwarded = JSON.parse(layer.getAttribute('data-props')!);
            expect(forwarded.active).toBe(true);
            expect(forwarded.activeTool).toBe('Draw');
            expect(forwarded.selectedId).toBe('a1');
            expect(forwarded.page).toBe(1);
            expect(props.onAddShape).not.toHaveBeenCalled();
        });
    });

    describe('pdf media', () => {
        it('renders PDF viewer with url, mediaName and layer props', () => {
            renderCanvas({
                mediaUrl: 'https://example.com/doc.pdf',
                mediaKind: 'pdf',
                mediaName: 'doc.pdf',
                activeTool: 'Comment',
            });
            const pdfMock = screen.getByTestId('workbench-pdf-mock');
            const forwarded = JSON.parse(pdfMock.getAttribute('data-props')!);
            expect(forwarded.url).toBe('https://example.com/doc.pdf');
            expect(forwarded.mediaName).toBe('doc.pdf');
            expect(forwarded.activeTool).toBe('Comment');
            expect(forwarded.annotations).toEqual([]);
        });

        it('does not render the image or the fallback state', () => {
            renderCanvas({ mediaUrl: 'https://example.com/doc.pdf', mediaKind: 'pdf' });
            expect(screen.queryByRole('img')).not.toBeInTheDocument();
            expect(screen.queryByTestId('icon-image-off')).not.toBeInTheDocument();
        });
    });

});