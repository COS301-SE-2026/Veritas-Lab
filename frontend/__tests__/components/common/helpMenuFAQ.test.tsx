import { render, screen, fireEvent } from '@testing-library/react';
import HelpMenuFAQ, { FAQS, filterFaqs } from '@/components/common/helpMenuFAQ';

describe('HelpMenuFAQ', () => {
    it('renders a button for every FAQ question', () => {
        render(<HelpMenuFAQ items={FAQS} openIndex={null} onToggle={jest.fn()} />);
        expect(screen.getAllByRole('button')).toHaveLength(FAQS.length);
        expect(screen.getByText(FAQS[0].question)).toBeInTheDocument();
    });

    it('hides answers when closed and shows the open one', () => {
        const { rerender } = render(
            <HelpMenuFAQ items={FAQS} openIndex={null} onToggle={jest.fn()} />,
        );
        expect(screen.queryByText(FAQS[0].answer)).not.toBeInTheDocument();

        rerender(<HelpMenuFAQ items={FAQS} openIndex={0} onToggle={jest.fn()} />);
        expect(screen.getByText(FAQS[0].answer)).toBeInTheDocument();
        expect(screen.getAllByRole('button')[0]).toHaveAttribute('aria-expanded', 'true');
    });

    it('calls onToggle with the index when clicked, and null when closing', () => {
        const onToggle = jest.fn();
        const { rerender } = render(
            <HelpMenuFAQ items={FAQS} openIndex={null} onToggle={onToggle} />,
        );
        fireEvent.click(screen.getByText(FAQS[1].question));
        expect(onToggle).toHaveBeenCalledWith(1);

        rerender(<HelpMenuFAQ items={FAQS} openIndex={1} onToggle={onToggle} />);
        fireEvent.click(screen.getByText(FAQS[1].question));
        expect(onToggle).toHaveBeenCalledWith(null);
    });

    it('renders nothing when there are no items', () => {
        render(<HelpMenuFAQ items={[]} openIndex={null} onToggle={jest.fn()} />);
        expect(screen.queryAllByRole('button')).toHaveLength(0);
    });
    
    it('returns every FAQ for an empty query', () => {
        expect(filterFaqs('')).toEqual(FAQS);
        expect(filterFaqs('   ')).toEqual(FAQS);
    });
    
    it('filters by question text', () => {
        const result = filterFaqs('password');
        expect(result).toHaveLength(1);
        expect(result[0].question).toContain('password');
    });
    
    it('filters by answer text', () => {
        const result = filterFaqs('administrator');
        expect(result.length).toBeGreaterThan(0);
    });
    
    it('returns an empty array when nothing matches', () => {
        expect(filterFaqs('abcdefgh12345')).toEqual([]);
    });
    
    it('is case insensitive', () => {
        expect(filterFaqs('PASSWORD')).toEqual(filterFaqs('password'));
    });
});
