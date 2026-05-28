import type { ChangeEvent, ReactNode } from 'react';
import type { DashboardCase } from '@/types/api';
import type { SortKey, StatusFilter } from '@/types/hooks';

export type CaseCardProps = {
    caseTitle: string;
    caseDescription: string;
    caseStatus: 'Open' | 'Closed' | 'In Progress';
    href?: string;
};

export type DashboardCardsProps = {
    cases?: DashboardCase[];
};

export type EvidenceCardProps = {
    mediaName: string;
    mediaUrl: string;
    mediaExtension: string;
};

export type DashboardModalProps = {
    isOpen: boolean;
    onClose: () => void;
    onCreated?: () => void;
};

export type DashboardBarProps = {
    searchValue?: string;
    onSearchChange?: (value: string) => void;
    statusFilter?: StatusFilter;
    onStatusChange?: (filter: StatusFilter) => void;
    sortValue?: SortKey;
    onSortChange?: (value: SortKey) => void;
};

export type MediaUploadModalProps = {
    isOpen: boolean;
    onClose: () => void;
    caseId?: string;
    onUploaded?: () => void | Promise<void>;
};

export type CheckBoxProps = {
    label: string;
    onChange: (event: ChangeEvent<HTMLInputElement>) => void;
    checked?: boolean;
    defaultChecked?: boolean;
    disabled?: boolean;
    className?: string;
};

export type DropdownOption = {
    label: string;
    value: string;
};

export type DropdownProps = {
    options: DropdownOption[];
    onChange?: (event: ChangeEvent<HTMLSelectElement>) => void;
    defaultValue?: string;
    disabled?: boolean;
    className?: string;
    optionClassName?: string;
};

export type ContainerProps = {
    children: ReactNode;
    className?: string;
};

export type ButtonProps = {
    children?: ReactNode;
    text?: string;
    onClick?: () => void;
    disabled?: boolean;
    type?: 'button' | 'submit' | 'reset';
    variant?: 'primary' | 'secondary' | 'outline' | 'sidebar' | 'submit' | 'sadSack';
    size?: 'small' | 'medium' | 'large';
    className?: string;
};

export type CardProps = {
    header: string | ReactNode;
    content: string | ReactNode;
    footer: string | ReactNode;
    className?: string;
    headerClassName?: string;
    contentClassName?: string;
    footerClassName?: string;
};

export type HeadingProps = {
    text: string;
};

export type InputProps = {
    placeholder?: string;
    value?: string;
    onChange?: (value: string) => void;
    id?: string;
    type?: string;
    className?: string;
    required?: boolean;
};

export type labelProps = {
    text: string;
    htmlFor: string;
    className?: string;
};

export type ModalProps = {
    children: ReactNode;
    isOpen: boolean;
    onClose: () => void;
};

export type SliderBarProps<T extends string = string> = {
    filters: ReadonlyArray<T>;
    defaultFilter?: T;
    onChange?: (filter: T) => void;
    className?: string;
};

export type TextProps = {
    text: string;
    className?: string;
};
