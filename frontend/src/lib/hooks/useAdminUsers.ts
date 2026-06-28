'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import { changeUserRole, deleteUser, fetchUsers } from '@/lib/api/admin';
import type { AdminUser } from '@/types/api';
export type AdminRoleFilter = 'All' | AdminUser['role'];
export type AdminSortKey = 'id' | 'displayName' | 'username' | 'role';
//hook for managing all admin related tasks
const getDisplayName = (user: AdminUser) => {
    const fallbackName = `${user.firstName ?? ''} ${user.lastName ?? ''}`.trim();
    return user.displayName ?? user.fullName ?? (fallbackName || user.username);
};

const sortUsers = (users: AdminUser[], sortKey: AdminSortKey) => {
    return [...users].sort((left, right) => {
        if(sortKey === 'id')
        {
            return left.id.localeCompare(right.id);
        }
        if(sortKey === 'displayName')
        {
            return getDisplayName(left).localeCompare(getDisplayName(right));
        }
        return left[sortKey].localeCompare(right[sortKey]);
    });
};

export default function useAdminUsers() {
    const [searchQuery, setSearchQuery] = useState('');
    const [roleFilter, setRoleFilter] = useState<AdminRoleFilter>('All');
    const [sortKey, setSortKey] = useState<AdminSortKey>('displayName');
    const [users, setUsers] = useState<AdminUser[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);
    const [pendingUserId, setPendingUserId] = useState<string | null>(null);
    const isMounted = useRef(true);
    const loadUsers = async () => {
        setIsLoading(true);
        setError(null);

        try
        {
            const fetchedUsers = await fetchUsers();
            if(isMounted.current)
            {
                setUsers(fetchedUsers);
            }
        }
        catch(loadError)
        {
            if(isMounted.current)
            {
                setError(loadError instanceof Error ? loadError.message : 'Failed to load users');
            }
        }
        finally
        {
            if(isMounted.current)
            {
                setIsLoading(false);
            }
        }
    };

    useEffect(() => {
        let isActive = true;
        void (async () => {
            setIsLoading(true);
            setError(null);

            try
            {
                const fetchedUsers = await fetchUsers();
                if(isActive)
                {
                    setUsers(fetchedUsers);
                }
            }
            catch(loadError)
            {
                if(isActive)
                {
                    setError(loadError instanceof Error ? loadError.message : 'Failed to load users');
                }
            }
            finally
            {
                if(isActive)
                {
                    setIsLoading(false);
                }
            }
        })();

        return () => {
            isMounted.current = false;
            isActive = false;
        };
    }, []);

    const visibleUsers = useMemo(() => {
        const normalizedQuery = searchQuery.trim().toLowerCase();

        const filtered = users.filter((user) => {
            const matchesRole = roleFilter === 'All' || user.role === roleFilter;

            if(!matchesRole)
            {
                return false;
            }

            if(!normalizedQuery)
            {
                return true;
            }
            const displayName = getDisplayName(user).toLowerCase();
            return(
                user.id.toLowerCase().includes(normalizedQuery) ||
                user.username.toLowerCase().includes(normalizedQuery) ||
                user.role.toLowerCase().includes(normalizedQuery) ||
                displayName.includes(normalizedQuery)
            );
        });

        return sortUsers(filtered, sortKey);
    }, [roleFilter, searchQuery, sortKey, users]);

    const updateUserRole = async (userId: string, nextRole: AdminUser['role']) => {
        setPendingUserId(userId);
        setActionError(null);
        try
        {
            await changeUserRole(userId, nextRole);
            await loadUsers();
        }
        catch(updateError)
        {
            setActionError(updateError instanceof Error ? updateError.message : 'Failed to update role');
        }
        finally
        {
            setPendingUserId(null);
        }
    };

    const removeUser = async (userId: string) => {
        setPendingUserId(userId);
        setActionError(null);

        try
        {
            await deleteUser(userId);
            await loadUsers();
        }
        catch(deleteError)
        {
            setActionError(deleteError instanceof Error ? deleteError.message : 'Failed to delete user');
        }
        finally 
        {
            setPendingUserId(null);
        }
    };

    return{
        searchQuery,
        setSearchQuery,
        roleFilter,
        setRoleFilter,
        sortKey,
        setSortKey,
        visibleUsers,
        isLoading,
        error,
        actionError,
        pendingUserId,
        updateUserRole,
        removeUser,
    };
}
//i think this is now done... but i may be back LOL