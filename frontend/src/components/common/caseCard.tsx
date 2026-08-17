import Link from 'next/link';
import type { CaseCardProps } from '@/types/components';
import CaseDeleteButton from './caseDeleteButton';

export default function CaseCard({ caseTitle, caseDescription, caseStatus, href, caseId, canDelete, onDeleted }: CaseCardProps) {
    const cardContent = (
        <div className="border rounded-lg p-4 shadow-md transition duration-150 hover:shadow-lg hover:border-[var(--color-primary)]">
            <div className="text-lg font-bold text-[var(--color-text)]">{caseTitle}</div>
            <p className="text-(--color-light)">{caseDescription}</p>
            <div className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-(--color-secondary) text-(--color-text)">
                {caseStatus}
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