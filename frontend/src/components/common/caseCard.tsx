import Link from 'next/link';
import type { CaseCardProps } from '@/types/components';

export default function CaseCard({ caseTitle, caseDescription, caseStatus, href }: CaseCardProps) {
    const cardContent = (
        <div className="border rounded-lg p-4 shadow-md transition duration-150 hover:shadow-lg hover:border-[var(--color-primary)]">
            <div className="text-lg font-bold text-[var(--color-text)]">{caseTitle}</div>
            <p className="text-(--color-light)">{caseDescription}</p>
            <div className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-(--color-secondary) text-(--color-text)">
                {caseStatus}
            </div>
        </div>
    );

    if (href) {
        return (
            <Link href={href} className="block rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:ring-offset-2">
                {cardContent}
            </Link>
        );
    }

    return cardContent;
}