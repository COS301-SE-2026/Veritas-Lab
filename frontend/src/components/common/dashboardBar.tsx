'use client';
import Input from '../ui/input';
import Dropdown from '../ui/dropdown';
import SliderBar from '../ui/sliderBar';
import type { SortKey, StatusFilter } from '@/lib/hooks/useCaseDashboard';

type DashboardBarProps = {
    searchValue?: string;
    onSearchChange?: (value: string) => void;
    statusFilter?: StatusFilter;
    onStatusChange?: (filter: StatusFilter) => void;
    sortValue?: SortKey;
    onSortChange?: (value: SortKey) => void;
};

export default function DashboardBar({
    searchValue,
    onSearchChange,
    statusFilter,
    onStatusChange,
    sortValue,
    onSortChange,
}: DashboardBarProps) {
    const statusFilters = ['All', 'Open', 'Closed'] as const;

    return (
        <>
        <div className='grid grid-cols-3 gap-4 rounded-full font-semibold text-[var(--color-text)] p-4 mt-4'>
            <div>
                <Input
                    placeholder="Search cases..."
                    className='shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] pl-5 w-full py-2.5 rounded-full'
                    value={searchValue}
                    onChange={onSearchChange}
                />
            </div>
            <div>
                <SliderBar
                    filters={statusFilters}
                    className='w-full'
                    defaultFilter={statusFilter}
                    onChange={onStatusChange}
                />
            </div>
            <div>
                <Dropdown
                    options={[
                        { label: 'Case Creation Date', value: 'caseCreationDate' },
                        { label: 'Case Name', value: 'caseName' },
                        { label: 'Case Creator', value: 'caseCreator' },
                    ]}
                    className='shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] pl-5 ml-3 w-full py-3.5 rounded-full'
                    optionClassName='shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] rounded-full'
                    defaultValue={sortValue}
                    onChange={(event) => onSortChange?.(event.target.value as SortKey)}
                />
            </div>
        </div>
        </>
    );
}