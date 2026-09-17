'use client';
import { Document, Page, pdfjs } from 'react-pdf';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

type PdfThumbnailProps = {
    url: string;
    width?: number;
};

export default function PdfThumbnail({ url, width = 96 }: Readonly<PdfThumbnailProps>) {
    return (
        <Document
            file={url}
            loading={<span className="text-xs text-(--color-text-subtle)">Loading…</span>}
            error={<span className="text-xs text-[var(--color-danger)]">No preview</span>}
        >
            <Page
                pageNumber={1}
                width={width}
                renderTextLayer={false}
                renderAnnotationLayer={false}
            />
        </Document>
    );
}