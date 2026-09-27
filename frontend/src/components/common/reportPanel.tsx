import { X, ShieldCheck, ShieldQuestion, ShieldAlert, ShieldX, LucideIcon } from 'lucide-react';
import { getCertaintyMeta } from '@/lib/report';
import type { ReportPanelProps } from '@/types/workbench';

const certIcon: Record<number, LucideIcon> = {
    0: ShieldCheck,
    1: ShieldQuestion,
    2: ShieldAlert,
    3: ShieldX, //we should review these i chose them quite rushed and i think we might already be using one of them elsewhere.
};

export default function reportPanel({mediaUrl, mediaKind, mediaName, certainty, findings, onClose} : Readonly<ReportPanelProps>)  {

    const certaintyMeta = getCertaintyMeta(certainty);
    const CertaintyIcon = certainty !== null ? (certIcon[certainty] ?? ShieldQuestion) : ShieldQuestion;
    return (
        <>
        <div className="flex items-start justify-between gap-4">
                    <div>
                        <h2 className="text-xl font-bold text-(--color-text-strong)">Report</h2>
                        <p className="mt-1 text-xs text-(--color-text-muted)">{mediaName}</p>
                    </div>
                    {onClose && (
                        <button
                            type="button"
                            onClick={onClose}
                            aria-label="Close report"
                            className="rounded-[var(--radius-sm)] p-1.5 text-(--color-text-subtle) transition-colors hover:bg-(--color-surface-sunken) hover:text-(--color-text-strong)"
                        >
                            <X size={18} />
                        </button>
                    )}
                </div>

                <div className="flex shrink-0 items-center justify-center overflow-hidden rounded-[var(--radius-md)] border border-(--color-line) bg-(--color-surface-sunken)">
                    {mediaKind === 'image' && mediaUrl ? (
                        /* eslint-disable-next-line @next/next/no-img-element */
                        <img src={mediaUrl} alt={mediaName} className="max-h-80 w-full object-contain" />
                    ) : null}

                    {mediaKind === 'pdf' && mediaUrl ? (
                        <iframe src={mediaUrl} title={mediaName} className="h-80 w-full" />
                    ) : null}

                    {!mediaUrl || mediaKind === 'unsupported' ? (
                        <p className="p-8 text-sm text-(--color-text-subtle)">
                            Preview unavailable for this evidence.
                        </p>
                    ) : null}
                </div>

                <div
                    className="flex shrink-0 items-center gap-3 rounded-[var(--radius-md)] border p-4"
                    style={{ borderColor: `${certaintyMeta.colorVar}40`, backgroundColor: `${certaintyMeta.colorVar}14` }}
                >
                    <CertaintyIcon size={22} className="shrink-0" style={{ color: certaintyMeta.colorVar }} />
                    <div>
                        <p className="text-sm font-bold" style={{ color: certaintyMeta.colorVar }}>
                            {certaintyMeta.label}
                        </p>
                        <p className="text-sm text-(--color-text-strong)">
                            {certaintyMeta.description}
                        </p>
                    </div>
                </div>

                <div className="flex flex-col gap-2 pt-2">
                    <h3 className="text-sm font-bold text-(--color-text-strong)">Findings</h3>
                    {findings ? (
                        <p className="whitespace-pre-wrap text-sm leading-relaxed text-(--color-text-strong)">
                            {findings}
                        </p>
                    ) : (
                        <p className="text-sm text-(--color-text-subtle)">
                            No findings available yet for this evidence.
                        </p>
                    )}
                </div>
        </>
    )
}