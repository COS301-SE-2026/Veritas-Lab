import { render, screen, fireEvent } from '@testing-library/react';
import MediaUploadModal from '@/components/common/mediaUploadModal';

describe('MediaUploadModal', () => {
    const onClose = jest.fn();

    beforeEach(() => {
        onClose.mockClear();
    });
    //render tests
    it('does not render when closed', () => {
        render(<MediaUploadModal isOpen={false} onClose={onClose} />);
        expect(screen.queryByText('Upload Media')).not.toBeInTheDocument();
    });

    it('renders when open and handles file selection', () => {
        render(<MediaUploadModal isOpen onClose={onClose} />);
        const input = screen.getByLabelText('Upload Media') as HTMLInputElement;
        const file = new File(['file-content'], 'report.pdf', { type: 'application/pdf' });
        fireEvent.change(input, { target: { files: [file] } });
        expect(screen.getByText('report.pdf')).toBeInTheDocument();
    });
    
    it('calls onClose when clicking cancel', () => {
        render(<MediaUploadModal isOpen onClose={onClose} />);
        fireEvent.click(screen.getByText('Cancel'));
        expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when clicking overlay', () => {
        const { container } = render(<MediaUploadModal isOpen onClose={onClose} />);
        const overlay = container.querySelector('div.fixed.inset-0');

        if(!overlay)
        {
            throw new Error('Overlay not found');
        }

        fireEvent.click(overlay);
        expect(onClose).toHaveBeenCalledTimes(1);
    });
});
