'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/TextLayer.css';
import AnnotationLayer from '@/components/common/annotationLayer';
import { findTextRects, readSelectionRects } from '@/lib/pdfHighlights';
import type { Annotation, AnnotationPoint, AnnotationTool, HighlightAnnotation, HighlightRect } from '@/types/workbench';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const PAGE_WIDTH = 700;
const isHighlight = (a: Annotation): a is HighlightAnnotation => a.kind === 'highlight';

type WorkbenchPdfProps = {
    url: string;
    mediaName: string;
    active: boolean;
    activeTool: AnnotationTool;
    annotations: Annotation[];
    selectedId: string | null;
    onSelectAnnotation: (id: string | null) => void;
    onAddShape: (points: AnnotationPoint[], page: number) => void;
    onAddNote: (position: AnnotationPoint, text: string, page: number) => void;
    onAddHighlight: (text: string, rects: HighlightRect[], page: number) => void;
    onResolveHighlight: (id: string, rects: HighlightRect[]) => void;
};

type PdfPageProps = Omit<WorkbenchPdfProps, 'url' | 'mediaName'> & { pageNumber: number };

function PdfPage({
    pageNumber,
    active,
    activeTool,
    annotations,
    selectedId,
    onSelectAnnotation,
    onAddShape,
    onAddNote,
    onAddHighlight,
    onResolveHighlight,
}: Readonly<PdfPageProps>) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [isTextLayerReady, setIsTextLayerReady] = useState(false);

    const pageHighlights = annotations.filter(isHighlight).filter((h) => h.page === pageNumber);
    const unresolved = pageHighlights.filter((h) => h.rects === undefined);
    const unresolvedKey = unresolved.map((h) => h.id).join('|');

    useEffect(() => {
        const container = containerRef.current;
        if (!container || !isTextLayerReady || unresolved.length === 0) return;

        for (const highlight of unresolved) {
            onResolveHighlight(highlight.id, findTextRects(container, highlight.text));
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isTextLayerReady, unresolvedKey, pageNumber]);

    const handleMouseUp = useCallback(() => {
        const container = containerRef.current;
        if (!container || !active || activeTool !== 'Highlight') return;

        const selection = readSelectionRects(container);
        if (!selection) return;

        onAddHighlight(selection.text, selection.rects, pageNumber);
        window.getSelection()?.removeAllRanges();
    }, [active, activeTool, onAddHighlight, pageNumber]);

    return (
        <div
            ref={containerRef}
            onMouseUp={handleMouseUp}
            className="relative w-fit overflow-hidden rounded-[var(--radius-sm)] shadow-[var(--shadow-md)]"
        >
            <Page
                pageNumber={pageNumber}
                width={PAGE_WIDTH}
                renderTextLayer
                renderAnnotationLayer={false}
                onRenderTextLayerSuccess={() => setIsTextLayerReady(true)}
            />

            {/* Highlights sit above the page but below the annotation overlay. */}
            <div className="pointer-events-none absolute inset-0">
                {pageHighlights.map((highlight) => (
                    (highlight.rects ?? []).map((rect, index) => (
                        <span
                            key={`${highlight.id}-${index}`}
                            aria-hidden="true"
                            style={{
                                position: 'absolute',
                                left: `${rect.x}%`,
                                top: `${rect.y}%`,
                                width: `${rect.width}%`,
                                height: `${rect.height}%`,
                                backgroundColor: highlight.id === selectedId
                                    ? 'color-mix(in srgb, var(--color-secondary) 45%, transparent)'
                                    : highlight.source === 'AI'
                                        ? 'color-mix(in srgb, var(--color-danger) 28%, transparent)'
                                        : 'color-mix(in srgb, var(--color-primary) 28%, transparent)',
                                borderRadius: '2px',
                            }}
                        />
                    ))
                ))}
            </div>

            <AnnotationLayer
                page={pageNumber}
                active={active}
                activeTool={activeTool}
                annotations={annotations}
                selectedId={selectedId}
                onSelectAnnotation={onSelectAnnotation}
                onAddShape={onAddShape}
                onAddNote={onAddNote}
            />
        </div>
    );
}

export default function WorkbenchPdf({ url, ...pageProps }: Readonly<WorkbenchPdfProps>) {
    const [numPages, setNumPages] = useState(0);

    return (
        <div className="flex max-h-[75vh] flex-col items-center gap-4 overflow-auto rounded-[var(--radius-lg)] border border-(--color-line) bg-(--color-surface-sunken) p-4">
            <Document
                file={url}
                onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                loading={<p className="text-sm text-(--color-text-subtle)">Loading PDF…</p>}
                error={<p className="text-sm text-[var(--color-danger)]">Couldn’t load PDF.</p>}
            >
                {Array.from({ length: numPages }, (_, index) => index + 1).map((pageNumber) => (
                    <PdfPage key={pageNumber} pageNumber={pageNumber} {...pageProps} />
                ))}
            </Document>
        </div>
    );
}