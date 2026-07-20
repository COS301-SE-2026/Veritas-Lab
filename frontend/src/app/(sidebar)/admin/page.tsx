'use client';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCurrentUser, useUserRole } from '@/context/UserRoleContext';
import AdminUserSearchBar from '@/components/common/adminUserSearchBar';
import AdminUsersPanel from '@/components/common/adminUsersPanel';
import AdminDeleteModal from '@/components/common/adminDeleteModal';
import useAdminUsers from '@/lib/hooks/useAdminUsers';
import type { AdminUser } from '@/types/api';
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
        if(userRole !== 'ADMIN')
        {
            router.replace('/dashboard');
        }
    }, [router, userRole]);

    const sortOptions = useMemo(() => ([
        { label: 'User Name', value: 'displayName' },
        { label: 'Username', value: 'username' },
        { label: 'User ID', value: 'id' },
        { label: 'Role', value: 'role' },
    ]), []);
    if(userRole !== 'ADMIN')
    {
        return <div className='mt-8 ml-8 text-sm text-[var(--color-light)]'>Redirecting...</div>;
    }
    return(
        <div className='mt-8 ml-8 mr-8'>
            <div className='flex items-start justify-between gap-4'>
                <div>
                    <div className='text-[32px] font-bold text-[var(--color-text)]'>Admin</div>
                    <div className='text-[16px] text-[var(--color-light)]'>Manage users, roles, and account access</div>
                </div>
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
            <div className='mt-4 space-y-3'>
                {isLoading ? (
                    <div className='text-sm text-[var(--color-light)]'>Loading users...</div>
                ) : error ? (
                    <div className='text-sm text-[var(--color-error)]'>{error}</div>
                ) : visibleUsers.length === 0 ? (
                    <div className='text-sm text-[var(--color-light)]'>No users found.</div>
                ) : (
                    <AdminUsersPanel
                        users={visibleUsers}
                        isBusy={pendingUserId !== null}
                        currentUserId={currentUser?.id ?? ''}
                        onRoleChange={(userId, nextRole) => {
                            if(userId === currentUser?.id)
                            {
                                return;
                            }
                            void updateUserRole(userId, nextRole);
                        }}
                        onDelete={(user) => {
                            if(user.id === currentUser?.id)
                            {
                                return;
                            }
                            setDeleteTarget(user);
                        }}
                    />
                )}
            </div>
            {actionError ? (
                <div className='mt-4 text-sm text-[var(--color-error)]'>{actionError}</div>
            ) : null}

            <AdminDeleteModal
                isOpen={deleteTarget !== null}
                userLabel={deleteTarget ? `${deleteTarget.username} (${deleteTarget.id})` : 'this user'}
                isSubmitting={pendingUserId === deleteTarget?.id}
                onClose={() => setDeleteTarget(null)}
                onConfirm={() => {
                    if(!deleteTarget)
                    {
                        return;
                    }
                    void (async () => {
                        try
                        {
                            await removeUser(deleteTarget.id);
                            setDeleteTarget(null);
                        }
                        catch
                        {
                            //will be handled in hook
                        }
                    })();
                }}
            />
        </div>
    ); //i hate html :( this was hell.
}