import { render, screen } from '@testing-library/react';
import HelpMenuGuide, { GUIDES, filterGuides} from '@/components/common/helpMenuGuide';

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

    it('returns all guides for an empty query', () => {
        expect(filterGuides('')).toEqual(GUIDES);
    });

    it('filters by title', () => {
        const result = filterGuides('roles');

        expect(result).toHaveLength(1);
        expect(result[0].title).toContain('Roles');
    });

    it('filters by body', () => {
        const result = filterGuides('JWT');

        expect(result.length).toBeGreaterThan(0);
    });

    it('is case insensitive', () => {
        expect(filterGuides('ANNOTATION')).toEqual(filterGuides('annotation'));
    });

    it('returns an empty array when there is no match', () => {
        expect(filterGuides('xyzxyzxyz')).toEqual([]);
    });
});