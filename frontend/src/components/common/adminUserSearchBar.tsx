'use client';
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
        <div className='grid gap-4 rounded-full font-semibold text-[var(--color-text)] p-4 mt-4 md:grid-cols-3'>
            <div>
                <Input
                    placeholder={searchPlaceholder}
                    className='shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] pl-5 w-full py-2.5 rounded-full'
                    value={searchValue}
                    onChange={onSearchChange}
                />
            </div>
            <div>
                <SliderBar
                    filters={filters}
                    className='w-full'
                    defaultFilter={roleFilter}
                    onChange={onRoleChange}
                />
            </div>
            <div>
                <Dropdown
                    options={sortOptions}
                    className='shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] pl-5 w-full py-3.5 rounded-full'
                    optionClassName='shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] rounded-full'
                    defaultValue={sortValue}
                    onChange={(event) => onSortChange?.(event.target.value)}
                />
            </div>
        </div>
    );
}