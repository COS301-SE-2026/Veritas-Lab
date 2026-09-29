'use client';
import Button from '@/components/ui/button';
import Dropdown from '@/components/ui/dropdown';
import type { AdminUser } from '@/types/api';

type AdminUserCardProps = {
    user: AdminUser;
    isBusy?: boolean;
    currentUserId?: string;
    onRoleChange: (userId: string, role: AdminUser['role']) => void;
    onDelete: (user: AdminUser) => void;
};
//user list cards
const roleOptions = [
    { label: 'Admin', value: 'ADMIN' },
    { label: 'Investigator', value: 'INVESTIGATOR' },
    { label: 'User', value: 'USER' },
];
const getDisplayName = (user: AdminUser) => {
    const fallbackName = `${user.firstName ?? ''} ${user.lastName ?? ''}`.trim();
    return user.displayName ?? user.fullName ?? (fallbackName || user.username);
};

export default function AdminUserCard({ user, isBusy = false, currentUserId, onRoleChange, onDelete }: AdminUserCardProps) {
    const isCurrentUser = currentUserId === user.id;
    const displayName = getDisplayName(user);

    return (
        <div className='grid grid-cols-1 gap-4 rounded-[var(--radius-lg)] border border-(--color-line) bg-(--color-surface) p-4 transition-colors hover:border-(--color-line-strong) md:grid-cols-[1.2fr_2fr_1.4fr_1fr_auto] md:items-center'>
            <div className='font-mono text-xs text-(--color-text-muted)'>{user.id}</div>
            <div className='text-sm font-medium text-(--color-text-strong)'>{displayName}</div>
            <div className='text-sm text-(--color-text-muted)'>{user.username}</div>
            <div>
                {isCurrentUser ? (
                    <span className={'vl-badge'}>{user.role}</span>
                ) : (
                    <Dropdown
                        options={roleOptions}
                        defaultValue={user.role}
                        disabled={isBusy}
                        onChange={(event) => onRoleChange(user.id, event.target.value as AdminUser['role'])}
                        className='text-sm'
                    />
                )}
            </div>
            <div className='flex justify-start md:justify-end'>
                {isCurrentUser ? (
                    <span className='text-xs italic text-(--color-text-subtle) px-6'>You</span>
                ) : (
                    <Button
                        type='button'
                        onClick={() => onDelete(user)}
                        disabled={isBusy}
                        className='rounded-full px-3 py-1.5 text-sm font-semibold text-white bg-(--color-danger) transition-colors hover:bg-[var(--danger-soft)] hover:text-(--color-primary) disabled:cursor-not-allowed disabled:opacity-50'
                    >
                        Delete
                    </Button>
                )}
            </div>
        </div>
    );
}