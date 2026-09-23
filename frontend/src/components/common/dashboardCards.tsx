import { Folders, FolderOpen, FolderCheck } from 'lucide-react';
import type { DashboardCardsProps } from '@/types/components';

export default function DashboardCards({ cases = [] }: DashboardCardsProps) {
    const total = cases.length;
    const openCount = cases.filter(c => !c.caseClosed).length;
    const closedAllTime = cases.filter(c => c.caseClosed).length;

    const stats = [
        { label: 'Total Cases', hint: 'All time', value: total, Icon: Folders, tint: 'bg-(--color-b-50) text-(--color-b-600) ring-[color-mix(in_srgb,var(--b-500)_30%,transparent)]' },
        { label: 'Open Cases', hint: 'Currently active', value: openCount, Icon: FolderOpen, tint: 'bg-[var(--info-soft)] text-[var(--info-fg)] ring-[color-mix(in_srgb,var(--info-fg)_20%,transparent)]' },
        { label: 'Cases Closed', hint: 'All time', value: closedAllTime, Icon: FolderCheck, tint: 'bg-(--color-surface-sunken) text-(--color-text-muted) ring-(--color-line-strong)' },
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            {stats.map(({ label, hint, value, Icon, tint }) => (
                <div key={label} className="vl-card p-5">
                    <div className="flex items-start justify-between gap-3">
                        <div>
                            <p className="text-sm font-medium text-(--color-text-muted)">{label}</p>
                            <p className="mt-2 text-[30px] font-bold leading-none text-(--color-text-strong)">{value}</p>
                            <p className="mt-2 text-xs text-(--color-text-subtle)">{hint}</p>
                        </div>
                        <span className={`flex size-11 items-center justify-center rounded-2xl ring-1 ${tint}`}>
                            <Icon size={22} />
                        </span>
                    </div>
                </div>
            ))}
        </div>
    );
}
