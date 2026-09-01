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
describe('AdminPage (integration)', () => {
    const mockedFetchUsers = fetchUsers as jest.MockedFunction<typeof fetchUsers>;
    const mockedChangeUserRole = changeUserRole as jest.MockedFunction<typeof changeUserRole>;
    const mockedDeleteUser = deleteUser as jest.MockedFunction<typeof deleteUser>;
    beforeEach(() => {
        jest.resetAllMocks();
        mockUseUserRole.mockReturnValue('ADMIN');
        mockUseCurrentUser.mockReturnValue({ id: 'user-1', username: 'zeta.admin' });
        mockedFetchUsers.mockResolvedValue(baseUsers);
    });
    //rendering
    it('redirects non admins to the dashboard and renders nothing else', () => {
        mockUseUserRole.mockReturnValue('USER');
        render(<AdminPage />);
        expect(screen.getByText('Redirecting...')).toBeInTheDocument();
        expect(mockReplace).toHaveBeenCalledWith('/dashboard');
        expect(screen.queryByText('Admin')).not.toBeInTheDocument();
    });
    it('loads and displays users for an admin hiding controls on the current admins own row', async () => {
        render(<AdminPage />);
        expect(screen.getByText('Loading users...')).toBeInTheDocument();
        expect(await screen.findByText('Admin User')).toBeInTheDocument();
        expect(screen.getByText('Investigator One')).toBeInTheDocument();
        expect(screen.getByText('Regular User')).toBeInTheDocument();
        const ownRow = getRowContainer('zeta.admin');
        expect(within(ownRow).queryByRole('combobox')).not.toBeInTheDocument();
        expect(within(ownRow).queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument();
        const investigatorRow = getRowContainer('alpha.investigator');
        expect(within(investigatorRow).getByRole('combobox')).toBeInTheDocument();
        expect(within(investigatorRow).getByRole('button', { name: 'Delete' })).toBeInTheDocument();
    });
    //errors
    it('shows an error message when users fail to load', async () => {
        mockedFetchUsers.mockRejectedValue(new Error('Failed to fetch users'));
        render(<AdminPage />);
        expect(await screen.findByText('Failed to fetch users')).toBeInTheDocument();
    });
    it('shows an empty state when there are no users', async () => {
        mockedFetchUsers.mockResolvedValue([]);
        render(<AdminPage />);
        expect(await screen.findByText('No users found.')).toBeInTheDocument();
    });
    //filter
    it('filters the user list by search query', async () => {
        render(<AdminPage />);
        await screen.findByText('Admin User');
        fireEvent.change(screen.getByPlaceholderText('Search users...'), { target: { value: 'regular' } });
        expect(screen.getByText('Regular User')).toBeInTheDocument();
        expect(screen.queryByText('Admin User')).not.toBeInTheDocument();
        expect(screen.queryByText('Investigator One')).not.toBeInTheDocument();
    });
    it('filters the user list by role', async () => {
        render(<AdminPage />);
        await screen.findByText('Admin User');
        fireEvent.click(screen.getByRole('button', { name: 'INVESTIGATOR' }));
        expect(screen.getByText('Investigator One')).toBeInTheDocument();
        expect(screen.queryByText('Admin User')).not.toBeInTheDocument();
        expect(screen.queryByText('Regular User')).not.toBeInTheDocument();
    });
    it('sorts the user list by username', async () => {
        render(<AdminPage />);
        await screen.findByText('Admin User');
        fireEvent.change(screen.getByDisplayValue('User Name'), { target: { value: 'username' } });
        const allElements = Array.from(document.querySelectorAll('body *'));
        const positionOf = (text: string) => allElements.indexOf(screen.getByText(text));
        expect(positionOf('Investigator One')).toBeLessThan(positionOf('Regular User'));
        expect(positionOf('Regular User')).toBeLessThan(positionOf('Admin User'));
    });
    it('changes a users role and reflects it after reload', async () => {
        mockedChangeUserRole.mockResolvedValue(undefined);
        mockedFetchUsers.mockResolvedValueOnce(baseUsers);
        mockedFetchUsers.mockResolvedValueOnce([
            adminUser,
            { ...investigatorUser, role: 'ADMIN' },
            regularUser,
        ]);
        render(<AdminPage />);
        await screen.findByText('Admin User');
        const investigatorRow = getRowContainer('alpha.investigator');
        fireEvent.change(within(investigatorRow).getByRole('combobox'), { target: { value: 'ADMIN' } });
        await waitFor(() => expect(mockedChangeUserRole).toHaveBeenCalledWith('user-2', 'ADMIN'));
        await waitFor(() => expect(mockedFetchUsers).toHaveBeenCalledTimes(2));
    });
    it('shows an action error when a role change fails without navigating away', async () => {
        mockedChangeUserRole.mockRejectedValue(new Error('Failed to update user role'));
        render(<AdminPage />);
        await screen.findByText('Admin User');
        const investigatorRow = getRowContainer('alpha.investigator');
        fireEvent.change(within(investigatorRow).getByRole('combobox'), { target: { value: 'ADMIN' } });
        expect(await screen.findByText('Failed to update user role')).toBeInTheDocument();
        expect(screen.getByText('Investigator One')).toBeInTheDocument();
    });
    //deleting
    it('deletes a user via the confirmation modal and removes them after reload', async () => {
        mockedDeleteUser.mockResolvedValue(undefined);
        mockedFetchUsers.mockResolvedValueOnce(baseUsers);
        mockedFetchUsers.mockResolvedValueOnce([adminUser, regularUser]);
        render(<AdminPage />);
        await screen.findByText('Admin User');
        const investigatorRow = getRowContainer('alpha.investigator');
        fireEvent.click(within(investigatorRow).getByRole('button', { name: 'Delete' }));
        expect(await screen.findByText('This will permanently remove alpha.investigator (user-2) from the system.')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Delete user' }));
        await waitFor(() => expect(mockedDeleteUser).toHaveBeenCalledWith('user-2'));
        await waitFor(() => expect(screen.queryByText('Investigator One')).not.toBeInTheDocument());
        expect(screen.getByText('Regular User')).toBeInTheDocument();
        expect(mockedFetchUsers).toHaveBeenCalledTimes(2);
    });
    it('cancels the delete confirmation without deleting', async () => {
        render(<AdminPage />);
        await screen.findByText('Admin User');
        const investigatorRow = getRowContainer('alpha.investigator');
        fireEvent.click(within(investigatorRow).getByRole('button', { name: 'Delete' }));
        await screen.findByRole('button', { name: 'Delete user' });
        fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
        expect(mockedDeleteUser).not.toHaveBeenCalled();
        expect(screen.getByText('Investigator One')).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Delete user' })).not.toBeInTheDocument();
    });
    it('shows an action error when deletion fails', async () => {
        mockedDeleteUser.mockRejectedValue(new Error('Failed to delete user'));
        render(<AdminPage />);
        await screen.findByText('Admin User');
        const investigatorRow = getRowContainer('alpha.investigator');
        fireEvent.click(within(investigatorRow).getByRole('button', { name: 'Delete' }));
        fireEvent.click(screen.getByRole('button', { name: 'Delete user' }));
        expect(await screen.findByText('Failed to delete user')).toBeInTheDocument();
        expect(screen.getByText('Investigator One')).toBeInTheDocument();
    });
});