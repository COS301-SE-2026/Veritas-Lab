type CaseCardProps = {
    caseTitle: string;
    caseDescription: string;
    caseStatus: 'Open' | 'Closed' | 'In Progress';
};

export default function CaseCard({ caseTitle, caseDescription, caseStatus }: CaseCardProps) {
        return (
            <>
            <div className="border rounded-lg p-4 shadow-md">
                <div className="text-lg font-bold text-[var(--color-text)]">{caseTitle}</div>
                <p className="text-gray-600">{caseDescription}</p>
                <div className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-[var(--color-primary)] text-white">
                    {caseStatus}
                </div>
            </div>
            </>
        );
}