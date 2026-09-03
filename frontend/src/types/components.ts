import type { ChangeEvent, ReactNode } from 'react';
import type { DashboardCase } from '@/types/api';
import type { SortKey, StatusFilter } from '@/types/hooks';
import { LucideIcon } from 'lucide-react';

export type CaseCardProps = {
    caseTitle: string;
    caseDescription: string;
    caseStatus: 'Open' | 'Closed' | 'In Progress';
    href?: string;
    caseId?: string;
    canDelete?: boolean;
    onDeleted?: () => void | Promise<void>;
};
export type CaseEditButtonProps = {
    caseId: string;
    initialName: string;
    initialDescription: string;
    onUpdated?: () => void | Promise<void>;
    className?: string;
};
export type CaseDeleteButtonProps = {
    caseId: string;
    caseTitle: string;
    onDeleted?: () => void | Promise<void>;
};
export type CommentEditButtonProps = {
    caseId: string;
    commentId: number;
    initialComment: string;
    onUpdated?: (commentId: number, newComment: string) => void | Promise<void>;
    onDeleted?: (commentId: number) => void | Promise<void>;
};

export type DashboardCardsProps = {
    cases?: DashboardCase[];
};

export type EvidenceCardProps = {
    mediaName: string;
    mediaUrl: string;
    mediaExtension: string;
    href?: string;
    mediaId?: string;
    caseId?: string;
    canDelete?: boolean;
    onDeleted?: () => void | Promise<void>;
};
//case evidence delete
export type EvidenceDeleteButtonProps = {
    caseId: string;
    mediaId: string;
    mediaName: string;
    onDeleted?: () => void | Promise<void>;
};

export type DashboardModalProps = {
    isOpen: boolean;
    onClose: () => void;
    onCreated?: () => void;
};

export type ResetPasswordModalProps = {
    isOpen: boolean;
    onClose: () => void;
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

export type CaseCloseButtonProps = {
    caseId: string;
    onClosed: () => void | Promise<void>;
    className?: string;
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
    variant?: 'primary' | 'secondary' | 'outline' | 'sidebar' | 'submit' | 'sadSack' | 'light';
    size?: 'small' | 'medium' | 'large';
    className?: string;
};

export type CardProps = {
    children?: ReactNode;
    header?: string | ReactNode;
    content?: string | ReactNode;
    footer?: string | ReactNode;
    className?: string;
    headerClassName?: string;
    contentClassName?: string;
    footerClassName?: string;
};

export type CardSectionProps = {
    children: ReactNode;
    className?: string;
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
    children?: ReactNode;
    variant?: 'default' | 'error' | 'success' | 'info';
    text: string | null;
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

export interface Highlight {
    title: string;
    description: string;
    icon: LucideIcon;
}

export type Step = {
    number: string;
    title: string;
    description: string;
    icon: LucideIcon;
};

export type Audience = {
    title: string;
    description: string;
    icon: LucideIcon;
};