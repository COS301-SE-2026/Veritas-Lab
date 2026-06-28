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
