import Card from '@/components/ui/card';
import type { DashboardCase } from '@/api/dashboard';

type DashboardCardsProps = {
    cases?: DashboardCase[];
};
//made it so that the values are actually populated with real data now.
export default function DashboardCards({ cases = [] }: DashboardCardsProps) {
    const total = cases.length;
    const openCount = cases.filter(c => !c.caseClosed).length;
    const closedAllTime = cases.filter(c => c.caseClosed).length;

    return (
        <>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
            <div>
                <Card
                    header="Total Cases"
                    content={String(total)}
                    contentClassName='text-[24px] font-bold'
                    footer="All time"
                    className='text-[var(--color-text)] border border-(--color-light) rounded-[21px] p-4 bg-[var(--color-secondary)]/10'
                />
            </div>
            <div>
                <Card
                    header="Open Cases"
                    content={String(openCount)}
                    contentClassName='text-[24px] font-bold'
                    footer="Open"
                    className='text-[var(--color-text)] border border-gray-300 rounded-[21px] p-4 bg-[var(--color-primary)]/10'
                />
            </div>
            <div>
                <Card
                    header="Cases Closed"
                    content={String(closedAllTime)}
                    contentClassName='text-[24px] font-bold'
                    footer="Closed (all time)"
                    className='text-[var(--color-text)] border border-gray-300 rounded-[21px] p-4 bg-[var(--color-primary)]/10'
                />
            </div>
        </div>
        </>
    );
}