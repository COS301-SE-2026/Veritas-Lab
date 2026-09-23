'use client';
import type { ReactNode } from "react";
import Link from "next/link";
import Image from "next/image";
import dynamic from "next/dynamic";
import { useDraggable } from '@dnd-kit/react';
import { GripVertical, PenLine, Clock, ClockAlert } from "lucide-react";
import { getMediaKind } from "@/lib/media";
import { getCertaintyMeta } from "@/lib/report";
import type { EvidenceCardProps } from "@/types/components";
import DeleteEvidence from "./caseEvidenceDeleteButton";

const PdfThumbnail = dynamic(() => import("@/components/common/pdfThumbnail"), {
    ssr: false,
    loading: () => <span className="text-xs text-(--color-text-subtle)">Loading…</span>,
});

function formatCapturedAt(value: string): string | null {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return null;
    return new Intl.DateTimeFormat('en-ZA', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit', hour12: false,
    }).format(date);
}

export default function EvidenceCard({
    mediaName, mediaUrl, mediaExtension, href, mediaId, caseId, canDelete, onDeleted, variant,
    capturedAt, reportCertainty, annotationCount = 0, placed = false, selected = false,
}: Readonly<EvidenceCardProps>) {
    const isBoard = variant === 'case-board';
    const formattedTime = capturedAt ? formatCapturedAt(capturedAt) : null;

    const { ref, handleRef, isDragging } = useDraggable({
        id: `evidence-${mediaId ?? mediaName}`,
        data: { mediaId, caseId, mediaName },
        disabled: !isBoard,
    });

    const mediaKind = getMediaKind(mediaExtension);

    if (isBoard) {
        const certainty = getCertaintyMeta(reportCertainty);

        let thumby: ReactNode;
        if (mediaUrl && mediaKind === 'pdf') {
            thumby = <PdfThumbnail url={mediaUrl} width={52} />;
        } else if (mediaUrl && mediaKind === 'image') {
            thumby = (
                <Image src={mediaUrl} alt={mediaName} width={52} height={52} unoptimized
                       className="h-full w-full object-cover" />
            );
        } else {
            thumby = (
                <div className="font-mono text-[10px] font-semibold uppercase text-(--color-text-subtle)">
                    {mediaExtension.replace('.', '') || '—'}
                </div>
            );
        }
        const stateClasses = isDragging
            ? "border-(--color-secondary) shadow-(--shadow-pop) ring-2 ring-[color-mix(in_srgb,var(--color-secondary)_35%,transparent)] scale-[1.02]"
            : selected
                ? "border-(--color-secondary) shadow-(--shadow-md) ring-2 ring-[color-mix(in_srgb,var(--color-secondary)_25%,transparent)]"
                : "border-(--color-line) shadow-(--shadow-xs) hover:border-[color-mix(in_srgb,var(--color-secondary)_45%,var(--color-line))] hover:shadow-(--shadow-md)";

        return (
            <div
                ref={ref}
                data-testid="case-board-evidence-card"
                className={`group relative w-full min-w-0 overflow-hidden rounded-[var(--radius-md)] border bg-(--color-surface) transition-[box-shadow,border-color,opacity,transform] duration-200 ${stateClasses} ${placed && !isDragging ? "opacity-55" : ""}`}
            >
                <div className="flex items-center gap-2.5 py-2.5 pr-3 pl-2">
                    <button
                        ref={handleRef}
                        type="button"
                        aria-label={`Drag ${mediaName} onto the board`}
                        className="flex h-8 w-5 shrink-0 cursor-grab items-center justify-center rounded-md text-(--color-text-subtle) transition-colors hover:bg-(--color-surface-sunken) hover:text-(--color-text-muted) active:cursor-grabbing focus-visible:outline-none focus-visible:shadow-(--shadow-focus)"
                    >
                        <GripVertical size={14} />
                    </button>

                    <div className="flex h-[52px] w-[52px] shrink-0 items-center justify-center overflow-hidden rounded-[10px] border border-(--color-line) bg-(--color-surface-sunken)">
                        {thumby}
                    </div>
                    <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                            <p className="truncate text-[14px] leading-tight font-semibold text-(--color-text-strong)" title={mediaName}>
                                {mediaName}
                            </p>
                            <div className="shrink-0 rounded-full bg-(--color-surface-sunken) px-1.5 py-0.5 font-mono text-[9px] font-semibold uppercase leading-none text-(--color-text-muted)">
                                {mediaExtension.replace('.', '')}
                            </div>
                        </div>

                        {formattedTime && (
                            <time
                                dateTime={capturedAt ?? undefined}
                                suppressHydrationWarning
                                className="mt-1 flex items-center gap-1 font-mono text-[11px] text-(--color-text-muted)"
                            >
                                <Clock size={11} className="shrink-0" />
                                {formattedTime}
                            </time>
                        )}
                        {!formattedTime && (
                            <p className="mt-1 flex items-center gap-1 text-[11px] font-medium text-(--warn-fg)">
                                <ClockAlert size={11} className="shrink-0" />
                                No timestamp
                            </p>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-3 border-t border-(--color-line) bg-(--color-surface-muted) py-1.5 pr-3 pl-4 text-[11px] text-(--color-text-muted)">
                    <div className="flex min-w-0 items-center gap-1.5">
                        <div className="vl-dot shrink-0" style={{ color: certainty.colorVar }} />
                        <div className="truncate">{certainty.label}</div>
                    </div>
                    <div className="ml-auto flex shrink-0 items-center gap-2.5">
                        {annotationCount > 0 && (
                            <div className="flex items-center gap-1" title={`${annotationCount} annotation${annotationCount === 1 ? '' : 's'}`}>
                                <PenLine size={11} /> {annotationCount}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }

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
    );
}