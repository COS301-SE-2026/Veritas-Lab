import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../../../src/components/ui/button';

const mockOnClick = jest.fn();

beforeEach(() => {
  mockOnClick.mockClear();
});
// This is the ideal test suite for all the components. For now this will be the only comprehensive.
describe('Button', () => {
  // Rendering tests
  describe('Rendering', () => {
    it('renders the text prop', () => {
      render(<Button text="Click here" onClick={mockOnClick} />);
      expect(screen.getByRole('button')).toHaveTextContent('Click here');
    });
  });
// Default props tests
  describe('Default props', () => {
    it('is enabled by default', () => {
      render(<Button text="Click here" onClick={mockOnClick} />);
      expect(screen.getByRole('button')).not.toBeDisabled();
    });

    it('has type="button" by default', () => {
      render(<Button text="Click here" onClick={mockOnClick} />);
      expect(screen.getByRole('button')).toHaveAttribute('type', 'button');
    });
  });
// Prop tests
  describe('Props', () => {
    it('disables the button when disabled={true}', () => {
      render(<Button text="Click here" onClick={mockOnClick} disabled />);
      expect(screen.getByRole('button')).toBeDisabled();
    });

    it.each(['button', 'submit', 'reset'] as const)(
      'renders with type="%s"',
      (type) => {
        render(<Button text="Click here" onClick={mockOnClick} type={type} />);
        expect(screen.getByRole('button')).toHaveAttribute('type', type);
      }
    );
// Variant and size tests - just checking that they don't throw errors for now
    it.each(['primary', 'secondary', 'outline'] as const)(
      'renders without error for variant="%s"',
      (variant) => {
        expect(() =>
          render(<Button text="Click here" onClick={mockOnClick} variant={variant} />)
        ).not.toThrow();
      }
    );
// Size tests
    it.each(['small', 'medium', 'large'] as const)(
      'renders without error for size="%s"',
      (size) => {
        expect(() =>
          render(<Button text="Click here" onClick={mockOnClick} size={size} />)
        ).not.toThrow();
      }
    );
  });
// Interaction tests
  describe('Interactions', () => {
    it('calls onClick when clicked', () => {
      render(<Button text="Click here" onClick={mockOnClick} />);
      fireEvent.click(screen.getByRole('button'));
      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });
// Disabled button should not call onClick
    it('does not call onClick when clicked while disabled', () => {
      render(<Button text="Click here" onClick={mockOnClick} disabled />);
      fireEvent.click(screen.getByRole('button'));
      expect(mockOnClick).not.toHaveBeenCalled();
    });
// Multiple clicks should call onClick the correct number of times
    it('calls onClick only once per click', () => {
      render(<Button text="Click here" onClick={mockOnClick} />);
      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByRole('button'));
      expect(mockOnClick).toHaveBeenCalledTimes(3);
    });
  });
});