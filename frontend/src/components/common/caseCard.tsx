import Link from 'next/link';
import type { CaseCardProps } from '@/types/components';
import CaseDeleteButton from './caseDeleteButton';
import CaseAssignButton from './caseAssignButton';
import { getCertaintyMeta } from '@/lib/report';

const STATUS_BADGE: Record<CaseCardProps['caseStatus'], string> = {
    Open: 'vl-badge vl-badge-open',
    Closed: 'vl-badge vl-badge-closed',
    'In Progress': 'vl-badge vl-badge-progress',
};

export default function CaseCard({ caseTitle, caseDescription, caseStatus, href, caseId, canDelete, onDeleted, riskScore, evidenceCount, assignMode, onAssignmentChanged }: CaseCardProps) {
    const hasRiskScore = riskScore !== undefined && riskScore !== null && (evidenceCount !== undefined && evidenceCount !== null);
    const risk = hasRiskScore ? getCertaintyMeta(Math.round(riskScore as number)) : null;
    const showDelete = canDelete && caseId;
    const showAssign = !!assignMode && !!caseId;

    return (
        <div className="relative">
            <div className="vl-card vl-card-interactive p-5">
                {}
                {href ? (
                    <Link
                        href={href}
                        className="absolute inset-0 z-10 rounded-[var(--radius-lg)] focus:outline-none focus-visible:ring-2 focus-visible:ring-(--b-500) focus-visible:ring-offset-2"
                    >
                        <span className="sr-only">{caseTitle}</span>
                    </Link>
                ) : null}

                <div className="flex items-end justify-between gap-3">
                    <div className="min-w-0">
                        <div className="truncate text-lg font-bold text-(--color-text-strong)">{caseTitle}</div>
                        <p className="mt-1 truncate text-sm text-(--color-text-muted)">{caseDescription}</p>
                    </div>
                    <div className="relative z-20 flex shrink-0 items-center gap-2">
                        <span className={STATUS_BADGE[caseStatus]}>
                            {caseStatus}
                        </span>
                        {showAssign ? (
                            <CaseAssignButton
                                caseId={caseId as string}
                                caseTitle={caseTitle}
                                mode={assignMode as 'assign' | 'unassign'}
                                onChanged={onAssignmentChanged}
                            />
                        ) : null}
                    </div>
                </div>

                {risk && (
                    <div className="mt-4 flex items-center justify-between border-t border-(--color-line) pt-3">
                        <span className="text-xs font-medium uppercase tracking-wide text-(--color-text-subtle)">Average risk score</span>
                        <span
                            className="vl-badge shrink-0"
                            style={{
                                backgroundColor: `color-mix(in srgb, ${risk.colorVar} 12%, transparent)`,
                                color: risk.colorVar,
                                borderColor: `color-mix(in srgb, ${risk.colorVar} 35%, transparent)`,
                            }}
                        >
                            {(riskScore as number).toFixed(1)} | {risk.label}
                        </span>
                    </div>
                )}
            </div>

            {showDelete ? (
                <div className="absolute top-3 right-3 z-20">
                    <CaseDeleteButton caseId={caseId as string} caseTitle={caseTitle} onDeleted={onDeleted} />
                </div>
            ) : null}
        </div>
    );
}