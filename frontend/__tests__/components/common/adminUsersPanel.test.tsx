import { render, screen } from '@testing-library/react';
import AdminUsersPanel from '@/components/common/adminUsersPanel';
import type { AdminUser } from '@/types/api';

const users: AdminUser[] = [
    {
        id: '11111111-1111-1111-1111-111111111111',
        username: 'alpha.user',
        role: 'INVESTIGATOR',
    },
    {
        id: '22222222-2222-2222-2222-222222222222',
        username: 'beta.user',
        role: 'USER',
    },
];