import { Node, NodeProps } from '@xyflow/react'
import { getCertaintyMeta } from '@/lib/report';
import dynamic from 'next/dynamic';
import { getMediaKind } from '@/lib/media';
import { PenLine } from 'lucide-react';
import Image from 'next/image';
import Pin from '@/components/common/boardPin'
const PdfThumbnail = dynamic(() => import("@/components/common/pdfThumbnail"), {
    ssr: false,
    loading: () => <span className="text-xs text-(--color-text-subtle)">Loading...</span>,
});

export type EvidenceNodeData = {
    mediaId: string;
    mediaName: string;
    mediaUrl: string;
    mediaExtension: string;
    reportCertainty: number | null;
    annotationCount: number;
}


export default function EvidenceNode({ data, selected }: NodeProps<Node<EvidenceNodeData>>) {
    const certainty = getCertaintyMeta(data.reportCertainty);
    const mediaKind = getMediaKind(data.mediaExtension);

    let thumby;
    if (data.mediaUrl && mediaKind === 'pdf') {
            thumby = <PdfThumbnail url={data.mediaUrl} width={294} />;
    } else if (data.mediaUrl && mediaKind === 'image') {
        thumby = <Image src={data.mediaUrl} alt={data.mediaName} width={294} height={294} unoptimized className="h-full w-full object-cover" />
    } else {
        thumby = (
            <div className="font-mono text-[10px] font-semibold uppercase text-(--color-text-subtle)">
                {data.mediaExtension.replace('.', '')}
            </div>
        );
    }
    return (
        <div className={`relative w-90 overflow-hidden rounded-[var(--radius-md)] border bg-(--color-surface) text-left shadow-(--shadow-xs)
            ${selected ? 'border-(--color-secondary) ring-2 ring-[color-mix(in_srgb,var(--color-secondary)_25%,transparent)]' : 'border-(--color-line)'}`}>
            <Pin />
            <div className="pt-6 pb-2 pr-3 pl-4">
                <p className="truncate text-[13px] font-semibold text-(--color-text-strong)" title={data.mediaName}>
                    {data.mediaName}
                </p>
                <div className="mt-2 flex aspect-video w-full items-center justify-center overflow-hidden rounded-[10px] border border-(--color-line) bg-(--color-surface-sunken)">
                    {thumby}
                </div>
                <div className="flex items-center gap-3 py-1.5 text-[11px] text-(--color-text-muted)">
                    <div className="flex min-w-0 items-center gap-1.5">
                        <div className="vl-dot shrink-0" style={{ color: certainty.colorVar }} />
                        <div className="truncate">{certainty.label}</div>
                    </div>
                    <div className="ml-auto flex shrink-0 items-center gap-2.5">
                        <div className="flex items-center gap-1">
                            <PenLine size={11} /> {data.annotationCount}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}