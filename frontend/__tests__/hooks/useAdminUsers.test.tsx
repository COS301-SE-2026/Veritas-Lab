import { act, renderHook, waitFor } from '@testing-library/react';
import useAdminUsers from '@/lib/hooks/useAdminUsers';
import { changeUserRole, deleteUser, fetchUsers } from '@/lib/api/admin';
import type { AdminUser } from '@/types/api';

jest.mock('@/lib/api/admin', () => ({
    fetchUsers: jest.fn(),
    changeUserRole: jest.fn(),
    deleteUser: jest.fn(),
}));

const sampleUsers: AdminUser[] = [
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
    {
        id: '33333333-3333-3333-3333-333333333333',
        username: 'charlie.admin',
        role: 'ADMIN',
    },
];
//admin user jest testing to follow: