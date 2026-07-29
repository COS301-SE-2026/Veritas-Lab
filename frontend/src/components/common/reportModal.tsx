'use client';
import { X, ShieldCheck, ShieldQuestion, ShieldAlert, ShieldX, LucideIcon } from 'lucide-react';
import Modal from '@/components/ui/modal';
import { getCertaintyMeta } from '@/lib/report';
import type { ReportModalProps } from '@/types/workbench';
const certIcon: Record<number, LucideIcon> = {
    0: ShieldCheck,
    1: ShieldQuestion,
    2: ShieldAlert,
    3: ShieldX, //we should review these i chose them quite rushed and i think we might already be using one of them elsewhere.
};

export default function ReportModal({
    isOpen,
    onClose,
    mediaUrl,
    mediaKind,
    mediaName,
    certainty,
    findings,
}: Readonly<ReportModalProps>) {
    const certaintyMeta = getCertaintyMeta(certainty);
    const CertaintyIcon = certainty !== null ? (certIcon[certainty] ?? ShieldQuestion) : ShieldQuestion;

    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <div className="flex max-h-[80vh] w-full max-w-2xl flex-col gap-4 overflow-y-auto rounded-[21px] p-6">
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <h2 className="text-xl font-bold text-(--color-text)">Report</h2>
                        <p className="mt-1 text-xs text-(--color-light)">{mediaName}</p>
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="Close report"
                        className="rounded-lg p-1 text-(--color-light) transition-colors hover:bg-(--color-lightest) hover:text-(--color-text)"
                    >
                        <X size={18} />
                    </button>
                </div>

                <div className="shrink-0 flex items-center justify-center overflow-hidden rounded-xl border border-(--color-light) bg-(--color-lightest)">
                    {mediaKind === 'image' && mediaUrl ? (
                        <img src={mediaUrl} alt={mediaName} className="max-h-80 w-full object-contain" />
                    ) : null}

                    {mediaKind === 'pdf' && mediaUrl ? (
                        <iframe src={mediaUrl} title={mediaName} className="h-80 w-full" />
                    ) : null}

                    {!mediaUrl || mediaKind === 'unsupported' ? (
                        <p className="p-8 text-sm text-(--color-light)">
                            Preview unavailable for this evidence.
                        </p>
                    ) : null}
                </div>

                <div className="shrink-0 flex items-center gap-3 rounded-xl border border-(--color-light) p-3">
                    <CertaintyIcon
                        size={20}
                        className="shrink-0"
                        style={{ color: certaintyMeta.colorVar }}
                    />
                    <div>
                        <p
                            className="text-s font-semibold"
                            style={{ color: certaintyMeta.colorVar }}
                        >
                            {certaintyMeta.label}
                        </p>
                        <p className="text-sm text-(--color-text)">
                            {certaintyMeta.description}
                        </p>
                    </div>
                </div>

                <div className="flex flex-col gap-2 pt-4">
                    <h3 className="text-s font-bold text-(--color-text)">Findings</h3>
                    {findings ? (
                        <p className="whitespace-pre-wrap text-s text-(--color-text)">
                            {findings}
                        </p>
                    ) : (
                        <p className="text-s text-(--color-light)">
                            No findings available yet for this evidence.
                        </p>
                    )}
                </div>
            </div>
        </Modal>
    );
}