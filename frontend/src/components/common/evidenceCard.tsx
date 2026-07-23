'use client';
import type { ReactNode } from "react";
import Link from "next/link";
import Image from "next/image";
import dynamic from "next/dynamic";
import Card from "../ui/card";
import { getMediaKind } from "@/lib/media";
import type { EvidenceCardProps } from "@/types/components";

const PdfThumbnail = dynamic(() => import("@/components/common/pdfThumbnail"), {
    ssr: false,
    loading: () => <span className="text-xs text-(--color-light)">Loading…</span>,
});

export default function EvidenceCard({ mediaName, mediaUrl, mediaExtension, href }: Readonly<EvidenceCardProps>) {
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
                className="max-h-16 max-w-16 object-contain"
            />
        );
    } else {
        preview = <span className="text-xs text-(--color-light)">No preview</span>;
    }

    const card = (
        <Card
            header={mediaName}
            headerClassName="   text-[18px] font-semibold mb-2"
            content={(
                <div className="flex h-24 items-center justify-center overflow-hidden rounded-[14px] bg-black/5">
                    {preview}
                </div>
            )}
            contentClassName="text-[16px] text-(--color-light)"
            footer={mediaExtension}
            footerClassName="text-sm text-(--color-light)"
            className="shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] rounded-[21px] p-4 w-[228px] h-[200px] text-[var(--color-text)]"
        />
    );

    if (href) {
        return (
            <Link
                href={href}
                className="block rounded-[21px] transition hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:ring-offset-2"
            >
                {card}
            </Link>
        );
    }

    return card;
}