'use client';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUserRole } from '@/context/UserRoleContext';
import AdminUserSearchBar from '@/components/common/adminUserSearchBar';
import AdminUsersPanel from '@/components/common/adminUsersPanel';
import AdminDeleteModal from '@/components/common/adminDeleteModal';
import useAdminUsers from '@/lib/hooks/useAdminUsers';
import type { AdminUser } from '@/types/api';

export default function AdminPage() {
    const router = useRouter();
    const userRole = useUserRole();
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
}