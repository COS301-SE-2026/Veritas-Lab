'use client';
import type { ReactNode } from "react";
import Link from "next/link";
import Image from "next/image";
import dynamic from "next/dynamic";
import { getMediaKind } from "@/lib/media";
import type { EvidenceCardProps } from "@/types/components";
import DeleteEvidence from "./caseEvidenceDeleteButton"

const PdfThumbnail = dynamic(() => import("@/components/common/pdfThumbnail"), {
    ssr: false,
    loading: () => <span className="text-xs text-(--color-text-subtle)">Loading…</span>,
});

export default function EvidenceCard({ mediaName, mediaUrl, mediaExtension, href, mediaId, caseId, canDelete, onDeleted}: Readonly<EvidenceCardProps>) {
    const mediaKind = getMediaKind(mediaExtension);

    let preview: ReactNode;
    if (mediaUrl && mediaKind === 'pdf') {
        preview = <PdfThumbnail url={mediaUrl} width={96} />;
    } else if (mediaUrl && mediaKind === 'image') {
        preview = (
            <Image
                src={mediaUrl}
                alt={mediaName}
                width={64}
                height={64}
                unoptimized
                className="max-h-20 max-w-full object-contain"
            />
        );
    } else {
        preview = <span className="text-xs text-(--color-text-subtle)">No preview</span>;
    }

    const card = (
        <div className="vl-card vl-card-interactive flex h-[204px] w-[230px] flex-col p-4">
            <div className="truncate text-[16px] font-semibold text-(--color-text-strong)">{mediaName}</div>
            <div className="mt-3 flex flex-1 items-center justify-center overflow-hidden rounded-[14px] border border-(--color-line) bg-(--color-surface-sunken)">
                {preview}
            </div>
            <div className="mt-3 flex items-center justify-between">
                <span className="vl-badge vl-badge-neutral uppercase">{mediaExtension}</span>
            </div>
        </div>
    );

    const showDelete = canDelete && mediaId && caseId;
    const deleteButton = showDelete ? (
        <div className="absolute top-3 right-3 z-10">
            <DeleteEvidence caseId={caseId} mediaId={mediaId} mediaName={mediaName} onDeleted={onDeleted} />
        </div>
    ) : null;
    //keeping same structure as much as possible (i dont want to create errors out of nowhere in the tests or rendering) hence might look messy.
    if (href) {
        return (
            <div className="relative">
                <Link
                    href={href}
                    className="block rounded-[var(--radius-lg)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--b-500)_50%,transparent)] focus-visible:ring-offset-2"
                >
                    {card}
                </Link>
                {deleteButton}
            </div>
        );
    }

    return (
        <div className="relative">
            {card}
            {deleteButton}
        </div>
    )
}