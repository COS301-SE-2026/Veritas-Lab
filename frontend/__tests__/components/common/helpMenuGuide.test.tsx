import { render, screen } from '@testing-library/react';
import HelpMenuGuide, { GUIDES } from '@/components/common/helpMenuGuide';

describe('HelpMenuGuide', () => {
    it('renders a card for every guide', () => {
        render(<HelpMenuGuide items={GUIDES} />);
        expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(GUIDES.length);
    });

    it('renders the title and body of each guide', () => {
        render(<HelpMenuGuide items={GUIDES} />);
        GUIDES.forEach((g) => {
            expect(screen.getByText(g.title)).toBeInTheDocument();
            expect(screen.getByText(g.body)).toBeInTheDocument();
        });
    });

    it('renders only the items it is given', () => {
        render(<HelpMenuGuide items={[GUIDES[0]]} />);
        expect(screen.getByText(GUIDES[0].title)).toBeInTheDocument();
        expect(screen.queryByText(GUIDES[1].title)).not.toBeInTheDocument();
    });

    it('renders nothing when there are no items', () => {
        render(<HelpMenuGuide items={[]} />);
        expect(screen.queryAllByRole('heading', { level: 2 })).toHaveLength(0);
    });
});