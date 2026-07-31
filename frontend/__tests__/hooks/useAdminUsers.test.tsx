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
describe('useAdminUsers', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('loads users on mount and filters and sorts them', async () => {
        const mockedFetchUsers = fetchUsers as jest.MockedFunction<typeof fetchUsers>;
        mockedFetchUsers.mockResolvedValue(sampleUsers);
        const { result } = renderHook(() => useAdminUsers());
        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });
        expect(result.current.visibleUsers).toHaveLength(3);
        act(() => {
            result.current.setSearchQuery('beta.user');
        });
        expect(result.current.visibleUsers).toHaveLength(1);
        expect(result.current.visibleUsers[0].username).toBe('beta.user');
        act(() => {
            result.current.setRoleFilter('ADMIN');
        });
        expect(result.current.visibleUsers).toHaveLength(0);
        act(() => {
            result.current.setSearchQuery('');
            result.current.setRoleFilter('All');
            result.current.setSortKey('id');
        });
        expect(result.current.visibleUsers[0].id).toBe('11111111-1111-1111-1111-111111111111');
    });

    it('stores an error when loading users fails', async () => {
        const mockedFetchUsers = fetchUsers as jest.MockedFunction<typeof fetchUsers>;
        mockedFetchUsers.mockRejectedValue(new Error('Failed to load users'));
        const { result } = renderHook(() => useAdminUsers());
        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });
        expect(result.current.error).toBe('Failed to load users');
    });

    it('updates roles and reloads the user list', async () => {
        const mockedFetchUsers = fetchUsers as jest.MockedFunction<typeof fetchUsers>;
        const mockedChangeUserRole = changeUserRole as jest.MockedFunction<typeof changeUserRole>;
        mockedFetchUsers.mockResolvedValueOnce(sampleUsers).mockResolvedValueOnce([
            { ...sampleUsers[0], role: 'ADMIN' },
            sampleUsers[1],
            sampleUsers[2],
        ]);
        const { result } = renderHook(() => useAdminUsers());
        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });
        await act(async () => {
            await result.current.updateUserRole(sampleUsers[0].id, 'ADMIN');
        });
        expect(mockedChangeUserRole).toHaveBeenCalledWith(sampleUsers[0].id, 'ADMIN');
        expect(mockedFetchUsers).toHaveBeenCalledTimes(2);
        expect(result.current.visibleUsers[0].role).toBe('ADMIN');
    });

    it('deletes users and reloads the user list', async () => {
        const mockedFetchUsers = fetchUsers as jest.MockedFunction<typeof fetchUsers>;
        const mockedDeleteUser = deleteUser as jest.MockedFunction<typeof deleteUser>;
        mockedFetchUsers.mockResolvedValueOnce(sampleUsers).mockResolvedValueOnce([
            sampleUsers[1],
            sampleUsers[2],
        ]);
        const { result } = renderHook(() => useAdminUsers());
        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });
        await act(async () => {
            await result.current.removeUser(sampleUsers[0].id);
        });
        expect(mockedDeleteUser).toHaveBeenCalledWith(sampleUsers[0].id);
        expect(mockedFetchUsers).toHaveBeenCalledTimes(2);
        expect(result.current.visibleUsers).toHaveLength(2);
        expect(result.current.visibleUsers.find((user) => user.id === sampleUsers[0].id)).toBeUndefined();
    });

    it('keeps cleanup safe if the hook unmounts during load', async () => {
        let resolveUsers!: (users: AdminUser[]) => void;
        const pendingFetch = new Promise<AdminUser[]>((resolve) => {
            resolveUsers = resolve;
        });
        const mockedFetchUsers = fetchUsers as jest.MockedFunction<typeof fetchUsers>;
        mockedFetchUsers.mockReturnValue(pendingFetch);
        const { unmount } = renderHook(() => useAdminUsers());
        unmount();
        resolveUsers(sampleUsers);
        await act(async () => {
            await pendingFetch;
        });
        expect(mockedFetchUsers).toHaveBeenCalledTimes(1);
    });
});