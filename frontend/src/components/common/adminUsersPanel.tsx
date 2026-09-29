'use client';
import type { AdminUser } from '@/types/api';
import AdminUserCard from '@/components/common/adminUserCard';

type AdminUsersPanelProps = {
    users: AdminUser[];
    isBusy?: boolean;
    currentUserId?: string;
    onRoleChange: (userId: string, role: AdminUser['role']) => void;
    onDelete: (user: AdminUser) => void;
};

export default function AdminUsersPanel({ users, isBusy = false, currentUserId, onRoleChange, onDelete }: AdminUsersPanelProps) {
    return (
        <div className='vl-panel p-5 text-(--color-text-strong)'>
            <div className='hidden grid-cols-[1.2fr_2fr_1.4fr_1fr_auto] gap-4 px-4 pb-3 text-xs font-semibold uppercase tracking-[0.14em] text-(--color-text-subtle) md:grid'>
                <div>ID</div>
                <div>Name &amp; Surname</div>
                <div>Username</div>
                <div>Role</div>
                <div className="text-right">Actions</div>
            </div>
            <div className='space-y-3'>
                {users.map((user) => (
                    <AdminUserCard
                        key={user.id}
                        user={user}
                        isBusy={isBusy}
                        currentUserId={currentUserId}
                        onRoleChange={onRoleChange}
                        onDelete={onDelete}
                    />
                ))}
            </div>
        </div>
    );
}