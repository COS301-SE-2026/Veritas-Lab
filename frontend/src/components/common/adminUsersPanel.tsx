'use client';
import Card from '@/components/ui/card';
import type { AdminUser } from '@/types/api';
import AdminUserCard from '@/components/common/adminUserCard';

type AdminUsersPanelProps = {
    users: AdminUser[];
    isBusy?: boolean;
    onRoleChange: (userId: string, role: AdminUser['role']) => void;
    onDelete: (user: AdminUser) => void;
};
//panel for the users
export default function AdminUsersPanel({ users, isBusy = false, onRoleChange, onDelete }: AdminUsersPanelProps) {
    return (
        <Card
            header={(
                <div className='grid grid-cols-1 gap-4 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--color-light)] md:grid-cols-[1.2fr_2fr_1.4fr_1fr_auto]'>
                    <div>ID</div>
                    <div>Name &amp; Surname</div>
                    <div>Username</div>
                    <div>Role</div>
                    <div>Actions</div>
                </div>
            )}
            content={(
                <div className='space-y-3'>
                    {users.map((user) => (
                        <AdminUserCard
                            key={user.id}
                            user={user}
                            isBusy={isBusy}
                            onRoleChange={onRoleChange}
                            onDelete={onDelete}
                        />
                    ))}
                </div>
            )}
            footer={''}
            className='rounded-[24px] border border-[var(--color-light)]/25 bg-[var(--color-secondary)]/8 p-5 text-[var(--color-text)]'
            headerClassName='mb-4'
            contentClassName=''
            footerClassName='hidden'
        />
    );
}