import { render, screen, fireEvent } from '@testing-library/react';
import Modal from '@/components/ui/modal';

const mockOnClose = jest.fn();

describe('Modal', () => {

    beforeEach(() => {
        mockOnClose.mockClear();
    });
    // Basic rendering tests
    it('renders nothing when isOpen is false', () => {
        render(
            <Modal isOpen={false} onClose={mockOnClose}>
                <p>Modal Content</p>
            </Modal>
        );
        expect(screen.queryByText('Modal Content')).not.toBeInTheDocument();
    });

    it('renders children when isOpen is true', () => {
        render(
            <Modal isOpen={true} onClose={mockOnClose}>
                <p>Modal Content</p>
            </Modal>
        );
        expect(screen.getByText('Modal Content')).toBeInTheDocument();
    });
});