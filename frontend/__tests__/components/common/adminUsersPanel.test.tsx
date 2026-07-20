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

describe('AdminUsersPanel', () => {
    it('renders the user table headings and user cards', () => {
        render(<AdminUsersPanel users={users} currentUserId='no-match' onRoleChange={jest.fn()} onDelete={jest.fn()} />);
        expect(screen.getByText('ID')).toBeInTheDocument();
        expect(screen.getByText('Name & Surname')).toBeInTheDocument();
        expect(screen.getByText('Username')).toBeInTheDocument();
        expect(screen.getByText('Role')).toBeInTheDocument();
        expect(screen.getByText('Actions')).toBeInTheDocument();
        expect(screen.getAllByText('alpha.user')).toHaveLength(2);
        expect(screen.getAllByText('beta.user')).toHaveLength(2);
        expect(screen.getAllByRole('button', { name: 'Delete' })).toHaveLength(2);
    });

    it('passes busy state to the user cards', () => {
        render(<AdminUsersPanel users={users} isBusy currentUserId='no-match' onRoleChange={jest.fn()} onDelete={jest.fn()} />);
        expect(screen.getAllByRole('combobox')).toHaveLength(2);
        expect(screen.getAllByRole('combobox')[0]).toBeDisabled();
    });

    it('hides current admin row actions', () => {
        render(
            <AdminUsersPanel
                users={users}
                currentUserId={users[0].id}
                onRoleChange={jest.fn()}
                onDelete={jest.fn()}
            />
        );
        expect(screen.getAllByRole('combobox')).toHaveLength(1);
        expect(screen.getAllByRole('button', { name: 'Delete' })).toHaveLength(1);
    });
});