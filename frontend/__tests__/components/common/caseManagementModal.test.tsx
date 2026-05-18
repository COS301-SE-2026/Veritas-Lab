import { render, screen, } from '@testing-library/react';
import CaseManagementModal from '@/components/common/caseManagementModal';

const mockOnClose = jest.fn();

describe('CaseManagementModal', () => {

    beforeEach(() => {
        mockOnClose.mockClear();
    });

    it('render nothing when isOpen false', () => {
        render(
            <CaseManagementModal isOpen={false} onClose={mockOnClose} />
        );
        expect(screen.queryByText('Create New Case')).not.toBeInTheDocument();
    });

    it('render modal when isOpen true', () => {
        render(
            <CaseManagementModal isOpen={true} onClose={mockOnClose} />
        );
        expect(screen.getByText('Create New Case')).toBeInTheDocument();
    });

    it('renders the case title input', () => {
        render(<CaseManagementModal isOpen={true} onClose={mockOnClose} />);
        expect(screen.getByPlaceholderText('Enter case title')).toBeInTheDocument();
    });

    it('renders the case description input', () => {
        render(<CaseManagementModal isOpen={true} onClose={mockOnClose} />);
        expect(screen.getByPlaceholderText('Enter case description')).toBeInTheDocument();
    });

    it('renders both the cancel and the create buttons', () => {
        render(<CaseManagementModal isOpen={true} onClose={mockOnClose}/>);
        expect(screen.getByText('Cancel')).toBeInTheDocument();
        expect(screen.getByText('Create Case')).toBeInTheDocument();
    })
});