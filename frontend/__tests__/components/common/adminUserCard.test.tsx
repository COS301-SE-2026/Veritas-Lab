import { fireEvent, render, screen } from '@testing-library/react';
import AdminUserCard from '@/components/common/adminUserCard';
import type { AdminUser } from '@/types/api';

const sampleUser: AdminUser = {
    id: '123e4567-e89b-12d3-a456-426614174000',
    username: 'jane.doe',
    role: 'USER',
};
// jest testing for the admin user card:
describe('AdminUserCard', () => {
    it('renders the user details and role selector', () => {
        render(<AdminUserCard user={sampleUser} onRoleChange={jest.fn()} onDelete={jest.fn()} />);
        expect(screen.getByText(sampleUser.id)).toBeInTheDocument();
        expect(screen.getAllByText(sampleUser.username)).toHaveLength(2);
        expect(screen.getByRole('combobox')).toHaveValue('USER');
        expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();
    });

    it('calls role change and delete handlers', () => {
        const onRoleChange = jest.fn();
        const onDelete = jest.fn();
        render(<AdminUserCard user={sampleUser} onRoleChange={onRoleChange} onDelete={onDelete} />);
        fireEvent.change(screen.getByRole('combobox'), { target: { value: 'ADMIN' } });
        expect(onRoleChange).toHaveBeenCalledWith(sampleUser.id, 'ADMIN');
        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
        expect(onDelete).toHaveBeenCalledWith(sampleUser);
    });

    it('disabled actions while busy', () => {
        render(
            <AdminUserCard
                user={sampleUser}
                isBusy
                onRoleChange={jest.fn()}
                onDelete={jest.fn()}
            />
        );
        expect(screen.getByRole('combobox')).toBeDisabled();
        expect(screen.getByRole('button', { name: 'Delete' })).toBeDisabled();
    });

    it('hides controls for the signed-in admin', () => {
        render(
            <AdminUserCard
                user={sampleUser}
                currentUserId={sampleUser.id}
                onRoleChange={jest.fn()}
                onDelete={jest.fn()}
            />
        );
        expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument();
    });
});