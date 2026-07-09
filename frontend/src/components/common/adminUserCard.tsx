'use client';
import Button from '@/components/ui/button';
import Dropdown from '@/components/ui/dropdown';
import type { AdminUser } from '@/types/api';

type AdminUserCardProps = {
    user: AdminUser;
    isBusy?: boolean;
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

export default function AdminUserCard({ user, isBusy = false, onRoleChange, onDelete }: AdminUserCardProps) {
    const displayName = getDisplayName(user);

    return(
        <div className='grid grid-cols-1 gap-4 rounded-[21px] border border-[var(--color-light)]/30 bg-white p-4 shadow-[inset_0_0_8px_rgba(0,0,0,0.06)] md:grid-cols-[1.2fr_2fr_1.4fr_1fr_auto] md:items-center'>
            <div className='text-sm font-semibold text-[var(--color-text)] break-all'>{user.id}</div>
            <div className='text-sm text-[var(--color-text)]'>{displayName}</div>
            <div className='text-sm text-[var(--color-text)]'>{user.username}</div>
            <div>
                <Dropdown
                    options={roleOptions}
                    defaultValue={user.role}
                    disabled={isBusy}
                    onChange={(event) => onRoleChange(user.id, event.target.value as AdminUser['role'])}
                    className='w-full rounded-full border border-[var(--color-light)]/40 px-4 py-2 text-sm text-[var(--color-text)]'
                />
            </div>
            <div className='flex justify-start md:justify-end'>
                <Button variant='sadSack' onClick={() => onDelete(user)} disabled={isBusy}>
                    <div className='text-sm font-semibold text-[var(--color-error)]'>Delete</div>
                </Button>
            </div>
        </div>
    );
}