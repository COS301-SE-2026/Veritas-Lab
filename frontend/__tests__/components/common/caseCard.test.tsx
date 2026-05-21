import {render, screen, fireEvent} from '@testing-library/react';
import CaseCard from '@/components/common/caseCard';

describe('CaseCard', () => {
    it('renders case information', () => {
        render(<CaseCard caseTitle="Mock Case" caseDescription="This is the description for Mock Case." caseStatus="Open" />);
        expect(screen.getByText('Mock Case')).toBeInTheDocument();
        expect(screen.getByText('This is the description for Mock Case.')).toBeInTheDocument();
        expect(screen.getByText('Open')).toBeInTheDocument();
    });
});