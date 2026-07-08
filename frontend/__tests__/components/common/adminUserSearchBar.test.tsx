import { fireEvent, render, screen } from '@testing-library/react';
import AdminUserSearchBar from '@/components/common/adminUserSearchBar';

describe('AdminUserSearchBar', () => {
    it('renders the admin user search controls', () => {
        render(<AdminUserSearchBar />);

        expect(screen.getByPlaceholderText('Search users...')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'All' })).toBeInTheDocument();
        expect(screen.getByText('User Name')).toBeInTheDocument();
    });

    it('supports searching, filtering, and sorting users', () => {
        const onSearchChange = jest.fn();
        const onRoleChange = jest.fn();
        const onSortChange = jest.fn();

        render(
            <AdminUserSearchBar
                searchValue=''
                onSearchChange={onSearchChange}
                roleFilter='All'
                onRoleChange={onRoleChange}
                sortValue='displayName'
                onSortChange={onSortChange}
            />
        );

        fireEvent.change(screen.getByPlaceholderText('Search users...'), { target: { value: 'jane' } });
        expect(onSearchChange).toHaveBeenCalledWith('jane');

        fireEvent.click(screen.getByRole('button', { name: 'ADMIN' }));
        expect(onRoleChange).toHaveBeenCalledWith('ADMIN');

        fireEvent.change(screen.getByRole('combobox'), { target: { value: 'username' } });
        expect(onSortChange).toHaveBeenCalledWith('username');
    });
});