'use client';
import { Search } from 'lucide-react';
import Input from '../ui/input';
import Dropdown from '../ui/dropdown';
import SliderBar from '../ui/sliderBar';

type AdminUserSearchBarProps = {
    searchValue?: string;
    onSearchChange?: (value: string) => void;
    searchPlaceholder?: string;
    filters?: readonly string[];
    roleFilter?: string;
    onRoleChange?: (filter: string) => void;
    sortValue?: string;
    sortOptions?: { label: string; value: string }[];
    onSortChange?: (value: string) => void;
};
//user search bar which is identical to the dsahboard basically.
export default function AdminUserSearchBar({
    searchValue,
    onSearchChange,
    searchPlaceholder = 'Search users...',
    filters = ['All', 'ADMIN', 'INVESTIGATOR', 'USER'],
    roleFilter,
    onRoleChange,
    sortValue,
    sortOptions = [
        { label: 'User Name', value: 'displayName' },
        { label: 'Username', value: 'username' },
        { label: 'User ID', value: 'id' },
        { label: 'Role', value: 'role' },
    ],
    onSortChange,
}: AdminUserSearchBarProps) {
    return (
        <div className='grid grid-cols-1 gap-3 md:grid-cols-3'>
            <div className="relative">
                <Search size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-(--color-text-subtle)" />
                <Input
                    placeholder={searchPlaceholder}
                    className='vl-input pl-11'
                    value={searchValue}
                    onChange={onSearchChange}
                />
            </div>
            <SliderBar
                filters={filters}
                className='w-full'
                defaultFilter={roleFilter}
                onChange={onRoleChange}
            />
            <Dropdown
                options={sortOptions}
                defaultValue={sortValue}
                onChange={(event) => onSortChange?.(event.target.value)}
            />
        </div>
    );
}