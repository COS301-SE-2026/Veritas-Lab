'use client';
import { Search } from 'lucide-react';
import Input from '../ui/input';
import Dropdown from '../ui/dropdown';
import SliderBar from '../ui/sliderBar';
import type { DashboardBarProps } from '@/types/components';
import type { SortKey } from '@/types/hooks';

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
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="relative">
                <Search size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-(--color-text-subtle)" />
                <Input
                    placeholder="Search cases..."
                    className="vl-input pl-11"
                    value={searchValue}
                    onChange={onSearchChange}
                />
            </div>
            <SliderBar
                filters={statusFilters}
                className="w-full"
                defaultFilter={statusFilter}
                onChange={onStatusChange}
            />
            <Dropdown
                options={[
                    { label: 'Case Creation Date', value: 'caseCreationDate' },
                    { label: 'Case Name', value: 'caseName' },
                    { label: 'Case Creator', value: 'caseCreator' },
                ]}
                defaultValue={sortValue}
                onChange={(event) => onSortChange?.(event.target.value as SortKey)}
            />
        </div>
    );
}