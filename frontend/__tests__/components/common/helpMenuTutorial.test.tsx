import { render, screen, fireEvent } from '@testing-library/react';
import HelpMenuTutorial, { TUTORIALS } from '@/components/common/helpMenuTutorial';

describe('HelpMenuTutorial', () => {
  it('renders the title and summary for every tutorial', () => {
    render(<HelpMenuTutorial items={TUTORIALS} openIndex={null} onToggle={jest.fn()} />);
    expect(screen.getAllByRole('button')).toHaveLength(TUTORIALS.length);
    TUTORIALS.forEach((t) => {
      expect(screen.getByText(t.title)).toBeInTheDocument();
      expect(screen.getByText(t.summary)).toBeInTheDocument();
    });
  });

  it('hides steps until the item is open', () => {
    const { rerender } = render(
      <HelpMenuTutorial items={TUTORIALS} openIndex={null} onToggle={jest.fn()} />,
    );
    expect(screen.queryByText(TUTORIALS[0].steps[0])).not.toBeInTheDocument();

    rerender(<HelpMenuTutorial items={TUTORIALS} openIndex={0} onToggle={jest.fn()} />);
    TUTORIALS[0].steps.forEach((s) => {
      expect(screen.getByText(s)).toBeInTheDocument();
    });
    expect(screen.getAllByRole('button')[0]).toHaveAttribute('aria-expanded', 'true');
  });

  it('renders the note only when the item has one and is open', () => {
    const withNote = TUTORIALS.findIndex((t) => t.note);
    render(
      <HelpMenuTutorial items={TUTORIALS} openIndex={withNote} onToggle={jest.fn()} />,
    );
    expect(screen.getByText('Note:')).toBeInTheDocument();
    expect(screen.getByText(TUTORIALS[withNote].note!)).toBeInTheDocument();
  });

  it('calls onToggle with the index when clicked, and null when closing', () => {
    const onToggle = jest.fn();
    const { rerender } = render(
      <HelpMenuTutorial items={TUTORIALS} openIndex={null} onToggle={onToggle} />,
    );
    fireEvent.click(screen.getByText(TUTORIALS[2].title));
    expect(onToggle).toHaveBeenCalledWith(2);

    rerender(<HelpMenuTutorial items={TUTORIALS} openIndex={2} onToggle={onToggle} />);
    fireEvent.click(screen.getByText(TUTORIALS[2].title));
    expect(onToggle).toHaveBeenCalledWith(null);
  });

  it('renders nothing when there are no items', () => {
    render(<HelpMenuTutorial items={[]} openIndex={null} onToggle={jest.fn()} />);
    expect(screen.queryAllByRole('button')).toHaveLength(0);
  });
});