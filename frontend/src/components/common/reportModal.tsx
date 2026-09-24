'use client';
import { useEffect } from 'react';

import type { ReportModalProps } from '@/types/workbench';
import ReportPanel from '@/components/common/reportPanel'


export default function ReportModal({
    isOpen,
    onClose,
    mediaUrl,
    mediaKind,
    mediaName,
    certainty,
    findings,
}: Readonly<ReportModalProps>) {
    useEffect(() => {
        if (!isOpen) return;
        const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
        document.addEventListener('keydown', onKey);
        return () => document.removeEventListener('keydown', onKey);
    }, [isOpen, onClose]);

    if (!isOpen) return null;



    return (
        <div
            className="vl-animate-fade fixed inset-0 z-50 flex items-center justify-center bg-[rgba(20,18,19,0.5)] p-4 backdrop-blur-sm"
            onClick={onClose}
            role="dialog"
            aria-modal="true"
        >
            <div
                onClick={(e) => e.stopPropagation()}
                className="vl-animate-pop flex max-h-[85vh] w-full max-w-2xl flex-col gap-4 overflow-y-auto rounded-[var(--radius-xl)] border border-(--color-line) bg-(--color-surface) p-6 shadow-[var(--shadow-pop)]"
            >
                <ReportPanel 
                    mediaUrl={mediaUrl}
                    mediaKind={mediaKind}
                    mediaName={mediaName}
                    certainty={certainty}
                    findings={findings}
                    onClose={onClose}
                />
            </div>
        </div>
    );
}