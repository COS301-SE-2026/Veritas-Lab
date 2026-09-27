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
    const cardContent = (
        <div className="vl-card vl-card-interactive p-5">
            <div className="flex items-end justify-between gap-3">
                <div className="min-w-0">
                    <div className="truncate text-lg font-bold text-(--color-text-strong)">{caseTitle}</div>
                    <p className="mt-1 truncate text-sm text-(--color-text-muted)">{caseDescription}</p>
                </div>
                <span className={`shrink-0 ${STATUS_BADGE[caseStatus]}`}>
                    {caseStatus}
                </span>
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
    );
    //this will work similar to how the evidence delete worked
    const showDelete = canDelete && caseId;
    const showAssign = !!assignMode && !!caseId;
    const actions = (showDelete || showAssign) ? (
        <div className="absolute top-3 right-3 z-10 flex items-center gap-2">
            {showAssign ? (
                <CaseAssignButton
                    caseId={caseId as string}
                    caseTitle={caseTitle}
                    mode={assignMode as 'assign' | 'unassign'}
                    onChanged={onAssignmentChanged}
                />
            ) : null}
            {showDelete ? (
                <CaseDeleteButton caseId={caseId as string} caseTitle={caseTitle} onDeleted={onDeleted} />
            ) : null}
        </div>
    ) : null;

    if (href) {
        return (
            <div className="relative">
                <Link
                    href={href}
                    className="block rounded-[var(--radius-lg)] focus:outline-none focus-visible:ring-2 focus-visible:ring-(--b-500) focus-visible:ring-offset-2"
                >
                    {cardContent}
                </Link>
                {actions}
            </div>
        );
    }
    return (
        <div className="relative">
            {cardContent}
            {actions}
        </div>
    );
}