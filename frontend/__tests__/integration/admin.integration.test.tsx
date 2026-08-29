import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import AdminPage from '@/app/(sidebar)/admin/page';
import { fetchUsers, changeUserRole, deleteUser } from '@/lib/api/admin';
import type { AdminUser } from '@/types/api';
jest.mock('@/lib/api/admin', () => ({
    fetchUsers: jest.fn(),
    changeUserRole: jest.fn(),
    deleteUser: jest.fn(),
}));
const mockUseUserRole = jest.fn();
const mockUseCurrentUser = jest.fn();
jest.mock('@/context/UserRoleContext', () => ({
    useUserRole: () => mockUseUserRole(),
    useCurrentUser: () => mockUseCurrentUser(),
}));
const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockRefresh = jest.fn();
jest.mock('next/navigation', () => ({
    useRouter: () => ({
        push: mockPush,
        replace: mockReplace,
        refresh: mockRefresh,
    }),
}));
const adminUser: AdminUser = {
    id: 'user-1',
    username: 'zeta.admin',
    role: 'ADMIN',
    displayName: 'Admin User',
};
const investigatorUser: AdminUser = {
    id: 'user-2',
    username: 'alpha.investigator',
    role: 'INVESTIGATOR',
    displayName: 'Investigator One',
};
const regularUser: AdminUser = {
    id: 'user-3',
    username: 'mid.user',
    role: 'USER',
    displayName: 'Regular User',
};
const baseUsers = [adminUser, investigatorUser, regularUser];
const getRowContainer = (usernameText: string) =>
    screen.getByText(usernameText).closest('div.grid') as HTMLElement;
//tests to come