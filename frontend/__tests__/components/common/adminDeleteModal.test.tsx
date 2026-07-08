import { fireEvent, render, screen } from '@testing-library/react';
import AdminDeleteModal from '@/components/common/adminDeleteModal';
//testing for delete modal actions
describe('AdminDeleteModal', () => {
    it('does not render when closed', () => {
        const { container } = render(
            <AdminDeleteModal
                isOpen={false}
                userLabel='jane.doe'
                onClose={jest.fn()}
                onConfirm={jest.fn()}
            />
        );
        expect(container).toBeEmptyDOMElement();
    });

    it('renders the confirmation copy and actions when open', () => {
        const onClose = jest.fn();
        const onConfirm = jest.fn();

        render(
            <AdminDeleteModal
                isOpen
                userLabel='jane.doe'
                onClose={onClose}
                onConfirm={onConfirm}
            />
        );
        //test that button inputs from user work
        expect(screen.getAllByText('Delete user')).toHaveLength(2);
        expect(screen.getByText('This will permanently remove jane.doe from the system.')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
        expect(onClose).toHaveBeenCalled();
        fireEvent.click(screen.getByRole('button', { name: 'Delete user' }));
        expect(onConfirm).toHaveBeenCalled();
    });

    it('shows a submitting state while deleting', () => {
        render(
            <AdminDeleteModal
                isOpen
                userLabel='jane.doe'
                isSubmitting
                onClose={jest.fn()}
                onConfirm={jest.fn()}
            />
        );

        expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled();
        expect(screen.getByRole('button', { name: 'Deleting' })).toBeDisabled();
    });
});