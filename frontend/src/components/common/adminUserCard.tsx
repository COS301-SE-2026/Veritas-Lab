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