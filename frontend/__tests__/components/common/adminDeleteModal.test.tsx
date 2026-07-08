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
});