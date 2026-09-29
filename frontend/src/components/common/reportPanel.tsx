import { X, ShieldCheck, ShieldQuestion, ShieldAlert, ShieldX, LucideIcon } from 'lucide-react';
import { getCertaintyMeta } from '@/lib/report';
import type { ReportPanelProps } from '@/types/workbench';

const certIcon: Record<number, LucideIcon> = {
    0: ShieldCheck,
    1: ShieldQuestion,
    2: ShieldAlert,
    3: ShieldX, //we should review these i chose them quite rushed and i think we might already be using one of them elsewhere.
};

export default function reportPanel({mediaUrl, mediaKind, mediaName, certainty, findings, onClose, heatmapUrl} : Readonly<ReportPanelProps>)  {

    const certaintyMeta = getCertaintyMeta(certainty);
    const CertaintyIcon = certainty !== null ? (certIcon[certainty] ?? ShieldQuestion) : ShieldQuestion;

    const importanceMeta = (importance: 'low' | 'medium' | 'high' | undefined) => {
        switch (importance) {
            case 'low':
                return { colorVar: 'var(--color-success)' };
            case 'medium':
                return { colorVar: 'var(--color-warning)' };
            case 'high':
                return { colorVar: 'var(--color-error)' };
            default:
                return { colorVar: 'var(--color-text-subtle)' };
        }
    };
    const order = ['high', 'medium', 'low'];

    const sortedReasons = (findings?.reasons ?? [])
        .map(r => typeof r === 'string' ? { message: r } : r)
        .sort((a, b) =>
            order.indexOf(a.importance ?? 'low') -
            order.indexOf(b.importance ?? 'low')
        );
    if (mediaKind === 'image') {

    }

    const getPercentage = (value: number | undefined) => {
        if (value === undefined) return 'N/A';
        return `${(value * 100).toFixed(2)}`;
    }
    return (
        <>
            <div className={`${onClose ? '' : 'vl-panel w-full max-h-160 overflow-y-auto'} flex flex-col gap-4 p-6`}>
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

                <div
                    className="flex flex-col shrink-0 gap-3 rounded-[var(--radius-md)] border p-4"
                    style={{ borderColor: `${certaintyMeta.colorVar}40`, backgroundColor: `${certaintyMeta.colorVar}14` }}
                >
                    <div className="flex items-center gap-3 border-b pb-5" style={{ borderColor: `${certaintyMeta.colorVar}40` }}>
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
                    <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">AI Generated Probability:</p>
                        <p className="text-2xl font-bold" style={{ color: certaintyMeta.colorVar }}>
                            {mediaKind === 'image' ? findings?.ai_probability?.toFixed(2) : getPercentage(findings?.ai_probability)}%
                        </p>
                    </div>
                    <div>
                        {mediaKind === 'video' && (
                            <>
                                <div className="flex items-center justify-between gap-3 py-3 border-t" style={{ borderColor: `${certaintyMeta.colorVar}40` }}>
                                    <p className='text-sm font-semibold text-(--color-text-muted)'>Video AI Probability:</p> 
                                    <p className="text-lg font-bold" style={{ color: certaintyMeta.colorVar }}>
                                        {getPercentage(findings?.visual?.ai_probability)}%
                                    </p>                              
                                    <p className='text-sm font-semibold text-(--color-text-muted)'>Audio AI Probability:</p> 
                                    <p className="text-lg font-bold" style={{ color: certaintyMeta.colorVar }}>
                                        {getPercentage(findings?.audio?.ai_probability)}%
                                    </p>
                                </div>
                                <div className="flex items-center justify-between gap-3 pt-3 border-t" style={{ borderColor: `${certaintyMeta.colorVar}40` }}>
                                    <p className='text-sm font-semibold text-(--color-text-muted)'>Visual weight:</p> 
                                    <p className="text-lg font-bold ml-5" style={{ color: certaintyMeta.colorVar }}>
                                        {getPercentage(findings?.fusion?.visual_weight)}%
                                    </p>
                                    <p className='text-sm font-semibold text-(--color-text-muted)'>Audio weight:</p> 
                                    <p className="text-lg font-bold" style={{ color: certaintyMeta.colorVar }}>
                                        {getPercentage(findings?.fusion?.audio_weight)}%
                                    </p>
                                </div>
                                <div>
                                    <p className="vl-panel text-sm text-(--color-text-muted) mt-3 p-3 rounded-[var(--radius-md)] border shadow-none" style={{ borderColor: `${certaintyMeta.colorVar}40`, backgroundColor: `${certaintyMeta.colorVar}14` }}>
                                        Note: The weights indicate the relative importance of each modality in the final decision.
                                    </p>
                                </div>
                            </>
                        )}
                    </div>
                </div>
                <div>
                    <div className="vl-panel flex flex-col gap-1 rounded-[var(--radius-md)] border p-4 shadow-none bg-(--color-surface-muted)">
                        <h3 className="mb-1 text-sm font-bold text-(--color-text-strong)">FINDINGS</h3>
                        <p className="text-sm text-(--color-text-strong)">
                                {findings?.findings}
                        </p>
                    </div>
                </div>
                {mediaKind === 'image' && (
                    <div className="flex flex-col gap-2 pt-2">
                        {findings ? (
                            <>
                            <div className="vl-panel flex flex-col gap-2 rounded-[var(--radius-md)] border p-4 shadow-none bg-(--color-surface-muted)">
                                <h3 className="text-sm font-bold text-(--color-text-strong)">REASONS</h3>
                                <div className="text-sm leading-relaxed text-(--color-text-strong)">
                                    {sortedReasons.map((reason, index) => {
                                        const simpleReason = typeof reason === 'string' ? { message: reason } : reason;
                                        return(
                                            <div key={index} className="vl-panel mb-2 p-4 rounded-[var(--radius-md)] shadow-none">
                                                <p className="text-sm font-semibold" style={{ color: importanceMeta(simpleReason?.importance).colorVar }}>
                                                    Importance {simpleReason?.importance}
                                                </p>
                                                <p>{simpleReason?.message}</p>
                                                <p className="text-sm font-semibold">
                                                    Suggests {simpleReason?.supports?.toLocaleLowerCase()}
                                                </p>
            
                                            </div>
                                        )
                                    })}
                                </div>

                            </div>
                            </>
                        ) : (
                            <p className="text-sm text-(--color-text-subtle)">
                                No reasons available yet for this evidence.
                            </p>
                        )}
                    </div>
                )}

                {mediaKind === 'pdf' && (
                    <>
                        <div className="flex flex-col gap-2 pt-2">
                            {findings ? (
                                <>
                                <div className="vl-panel flex flex-col gap-2 rounded-[var(--radius-md)] border p-4 shadow-none bg-(--color-surface-muted)">
                                    <h3 className="text-sm font-bold text-(--color-text-strong)">REASONS</h3>
                                    <div className="text-sm leading-relaxed text-(--color-text-strong)">
                                        {sortedReasons.map((reason, index) => {
                                            const simpleReason = typeof reason === 'string' ? { message: reason } : reason;
                                            return(
                                                <div key={index} className="vl-panel mb-2 p-4 rounded-[var(--radius-md)] shadow-none"> 
                                                    <p>{simpleReason?.message}</p>
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                                </>
                            ) : (
                                <p className="text-sm text-(--color-text-subtle)">
                                    No reasons available yet for this evidence.
                                </p>
                            )}
                        </div>
                    </>
                )}

                {mediaKind === 'video' && (
                    <>
                        <div className="flex flex-col gap-2 pt-2">
                            {findings ? (
                                <>
                                <div className="vl-panel flex flex-col gap-2 rounded-[var(--radius-md)] border p-4 shadow-none bg-(--color-surface-muted)">
                                    <h3 className="text-sm font-bold text-(--color-text-strong)">REASONS</h3>
                                    <p className="text-sm text-(--color-text-strong)">{findings.visual?.explanation}</p>
                                </div>
                                
                                </>
                            ) : (
                                <p className="text-sm text-(--color-text-subtle)">
                                    No reasons available yet for this evidence.
                                </p>
                            )}
                        </div>
                    </>
                )}
            </div>
        </>
    )
}