import Link from 'next/link';
import type { CaseCardProps } from '@/types/components';
import CaseDeleteButton from './caseDeleteButton';
import { getCertaintyMeta } from '@/lib/report';

export default function CaseCard({ caseTitle, caseDescription, caseStatus, href, caseId, canDelete, onDeleted, riskScore, evidenceCount }: CaseCardProps) {
    const hasRiskScore = riskScore !== undefined && riskScore !== null && (evidenceCount !== undefined && evidenceCount !== null);
    const risk = hasRiskScore ? getCertaintyMeta(Math.round(riskScore as number)) : null;
    const cardContent = (
        <div className="border rounded-lg p-4 shadow-md transition duration-150 hover:shadow-lg hover:border-[var(--color-primary)]">
            <div className="text-lg font-bold text-[var(--color-text)]">{caseTitle}</div>
            <p className="text-(--color-light)">{caseDescription}</p>
            <div className="justify-between flex mt-2 items-center">
                <div className="px-2 py-1 text-xs font-semibold rounded-full bg-(--color-secondary) text-(--color-text)">
                    {caseStatus}
                </div>
                {risk && (
                    <div
                            className="px-2 py-1 text-xs font-semibold rounded-full"
                            style={{ backgroundColor: `${risk.colorVar}20`, color: risk.colorVar }}
                        >
                        Average Risk Score: {riskScore} ({risk.label})
                    </div>
                )}
            </div>
        </div>
    );
    //this will work similar to how the evidence delete worked
    const showDelete = canDelete && caseId;
    const deleteButton = showDelete ? (
        <div className="absolute top-3 right-3 z-10">
            <CaseDeleteButton caseId={caseId} caseTitle={caseTitle} onDeleted={onDeleted} />
        </div>
    ) : null;

    if (href) {
        return (
            <div className="relative">
                <Link
                    href={href}
                    className="block rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:ring-offset-2"
                >
                    {cardContent}
                </Link>
                {deleteButton}
            </div>
        );
    }
    return (
        <div className="relative">
            {cardContent}
            {deleteButton}
        </div>
    );
}