import { render, screen, } from '@testing-library/react';
import CaseManagementBar from '@/components/common/caseManagementBar';

const mockOnCreateCase = jest.fn();

describe('CaseManagementBar', () => {

    beforeEach(() => {
        mockOnCreateCase.mockClear();
    });

    it('render the Search input', () => {
        render(<CaseManagementBar/>);
        expect(screen.getByPlaceholderText('Search cases...')).toBeInTheDocument();
    });

    it('render the Case status dropdown', () => {
        render(<CaseManagementBar/>);
        expect(screen.getByText('All Cases')).toBeInTheDocument();
    })

    it('render the Filter by dropdown', () => {
        render(<CaseManagementBar/>);
        expect(screen.getByText('Date Created')).toBeInTheDocument();
    });
});