import { render, screen } from '@testing-library/react';
import EvidenceCard from '@/components/common/evidenceCard';

//this will probably need to change after the implementation fo the case page as we may have added more attributes
describe('EvidenceCard', () => {
    it('renders file details', () => {
        render(
            <EvidenceCard
                fileName="EvidenceA.pdf"
                preview="Preview text" //could also be a preview of the image(a normal user will have the images blanked out to protect privacy)
                properties="Size: 2MB"
            />
        );
        expect(screen.getByText('EvidenceA.pdf')).toBeInTheDocument();
        expect(screen.getByText('Preview text')).toBeInTheDocument();
        expect(screen.getByText('Size: 2MB')).toBeInTheDocument();
    });
});
