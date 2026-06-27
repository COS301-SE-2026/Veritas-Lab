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
