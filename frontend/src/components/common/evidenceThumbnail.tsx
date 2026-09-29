'use client';
import dynamic from 'next/dynamic';
import { resolveMediaKind } from '@/lib/media';
import Image from 'next/image';
import { useState } from 'react';

type EvidenceThumbnailProps = {
    mediaUrl?: string | null;
    mediaName: string;
    mediaExtension: string;
    width: number;
    small?: boolean;
};

const PdfThumbnail = dynamic(() => import('@/components/common/pdfThumbnail'), { ssr: false });
export default function EvidenceThumbnail({ mediaUrl, mediaName, mediaExtension, width }: EvidenceThumbnailProps) {
    const [videoFailed, setVideoFailed] = useState(false);
    const mediaKind = resolveMediaKind({ mediaName, mediaExtension, mediaUrl });

    if (!mediaUrl) {
        return (
            <div className="font-semibold text-(--color-text-subtle)">
                {mediaExtension.replace('.', '').toUpperCase()}
            </div>
        )
    }
    if (mediaKind === 'image') {
        return <Image src={mediaUrl} width={width} height={width} alt={mediaName} unoptimized />;
    }
    if (mediaKind === 'pdf') { 
        return <PdfThumbnail url={mediaUrl} width={width} />;
    }
    if (mediaKind === 'video' && !videoFailed) {
        return (
            <div className="relative h-full w-full">
                <video
                    src={mediaUrl}
                    onError={() => setVideoFailed(true)}
                    className="pointer-events-none h-full w-full object-cover"
                />
            </div>
        )
    }
}