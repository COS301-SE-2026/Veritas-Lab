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