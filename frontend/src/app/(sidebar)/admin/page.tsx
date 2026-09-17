'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCurrentUser, useUserRole } from '@/context/UserRoleContext';
import AdminUserSearchBar from '@/components/common/adminUserSearchBar';
import AdminUsersPanel from '@/components/common/adminUsersPanel';
import AdminDeleteModal from '@/components/common/adminDeleteModal';
import useAdminUsers from '@/lib/hooks/useAdminUsers';
import type { AdminUser } from '@/types/api';
import Label from '@/components/ui/label';
//le admin page
export default function AdminPage() {
    const router = useRouter();
    const userRole = useUserRole();
    const currentUser = useCurrentUser(); //added to ensure admin cant delete itself or role change
    const [deleteTarget, setDeleteTarget] = useState<AdminUser | null>(null);

    const {
        searchQuery,
        setSearchQuery,
        roleFilter,
        setRoleFilter,
        sortKey,
        setSortKey,
        visibleUsers,
        updateUserRole,
        removeUser,
        isLoading,
        error,
        actionError,
        pendingUserId,
    } = useAdminUsers();

    useEffect(() => {
        if (userRole !== 'ADMIN') {
            router.replace('/dashboard');
        }
    }, [router, userRole]);

    const sortOptions = [
        { label: 'User Name', value: 'displayName' },
        { label: 'Username', value: 'username' },
        { label: 'User ID', value: 'id' },
        { label: 'Role', value: 'role' },
    ];
    if (userRole !== 'ADMIN') {
        return <div className='mx-auto max-w-7xl px-6 sm:px-8 pt-10 text-sm text-(--color-text-muted)'>Redirecting...</div>;
    }
    return (
        <div className='mx-auto max-w-7xl px-6 sm:px-8 pt-10 pb-16'>
            <div>
                <h1 className='text-[30px] sm:text-[34px] font-bold tracking-tight text-(--color-text-strong)'>Admin</h1>
                <p className='mt-1 text-[15px] text-(--color-text-muted)'>Manage users, roles, and account access</p>
            </div>
            <div className='mt-8'>
                <AdminUserSearchBar
                    searchValue={searchQuery}
                    onSearchChange={setSearchQuery}
                    searchPlaceholder='Search users...'
                    filters={['All', 'ADMIN', 'INVESTIGATOR', 'USER']}
                    roleFilter={roleFilter}
                    onRoleChange={(value) => setRoleFilter(value as 'All' | 'ADMIN' | 'INVESTIGATOR' | 'USER')}
                    sortValue={sortKey}
                    sortOptions={sortOptions}
                    onSortChange={(value) => setSortKey(value as 'id' | 'displayName' | 'username' | 'role')}
                />
            </div>
            <div className='mt-6 space-y-3'>
                {isLoading ? (
                    <div className='rounded-[var(--radius-lg)] border border-dashed border-(--color-line-strong) bg-(--color-surface) py-16 text-center text-sm text-(--color-text-muted)'>Loading users...</div>
                ) : error ? <Label text={error} htmlFor="error" variant="error" /> : visibleUsers.length === 0 ? (
                    <div className='rounded-[var(--radius-lg)] border border-dashed border-(--color-line-strong) bg-(--color-surface) py-16 text-center text-sm text-(--color-text-muted)'>No users found.</div>
                ) : (
                    <AdminUsersPanel
                        users={visibleUsers}
                        isBusy={pendingUserId !== null}
                        currentUserId={currentUser?.id ?? ''}
                        onRoleChange={(userId, nextRole) => {
                            if (userId === currentUser?.id) {
                                return;
                            }
                            void updateUserRole(userId, nextRole);
                        }}
                        onDelete={(user) => {
                            if (user.id === currentUser?.id) {
                                return;
                            }
                            setDeleteTarget(user);
                        }}
                    />
                )}
            </div>
            {actionError ? (
                <div className='mt-4 text-sm text-[var(--color-danger)]'>{actionError}</div>
            ) : null}

            <AdminDeleteModal
                isOpen={deleteTarget !== null}
                userLabel={deleteTarget ? `${deleteTarget.username} (${deleteTarget.id})` : 'this user'}
                isSubmitting={pendingUserId === deleteTarget?.id}
                onClose={() => setDeleteTarget(null)}
                onConfirm={() => {
                    if (!deleteTarget) {
                        return;
                    }
                    void (async () => {
                        try {
                            await removeUser(deleteTarget.id);
                            setDeleteTarget(null);
                        }
                        catch {
                            //will be handled in hook
                        }
                    })();
                }}
            />
        </div>
    );
}