'use client';
import { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import AnnotationLayer from '@/components/common/annotationLayer';
import type { Annotation, AnnotationPoint, AnnotationTool } from '@/types/workbench';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const PAGE_WIDTH = 700;

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
};

export default function WorkbenchPdf({
    url,
    active,
    activeTool,
    annotations,
    selectedId,
    onSelectAnnotation,
    onAddShape,
    onAddNote,
}: Readonly<WorkbenchPdfProps>) {
    const [numPages, setNumPages] = useState(0);

    return (
        <div className="flex max-h-[75vh] flex-col items-center gap-4 overflow-auto rounded-2xl border border-(--color-light) bg-black/5 p-4">
            <Document
                file={url}
                onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                loading={<p className="text-sm text-(--color-light)">Loading PDF…</p>}
                error={<p className="text-sm text-(--color-error)">Couldn’t load PDF.</p>}
            >
                {Array.from({ length: numPages }, (_, index) => index + 1).map((pageNumber) => (
                    <div key={pageNumber} className="relative w-fit shadow-md">
                        <Page pageNumber={pageNumber} width={PAGE_WIDTH} renderTextLayer={false} renderAnnotationLayer={false} />
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
                ))}
            </Document>
        </div>
    );
}