import Card from '@/components/ui/card';

export default function DashboardCards() {
    return (
        <>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
            <div>
                <Card
                    header="Total Cases"
                    content="15"
                    contentClassName='text-[24px] font-bold'
                    footer="All time"
                    className='text-[var(--color-text)] border border-gray-300 rounded-[21px] p-4 bg-[var(--color-primary)]/10'
                />
            </div>
            <div>
                <Card
                    header="Open Cases"
                    content="5"
                    contentClassName='text-[24px] font-bold'
                    footer="In progress"
                    className='text-[var(--color-text)] border border-gray-300 rounded-[21px] p-4 bg-[var(--color-primary)]/10'
                />
            </div>
            <div>
                <Card
                    header="Closed Cases this Week"
                    content="10"
                    contentClassName='text-[24px] font-bold'
                    footer="Resolved"
                    className='text-[var(--color-text)] border border-gray-300 rounded-[21px] p-4 bg-[var(--color-primary)]/10'
                />
            </div>
        </div>
        </>
    );
}