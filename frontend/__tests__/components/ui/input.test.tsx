import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Input from '../../../src/components/ui/input';

const mockOnChange = jest.fn();

beforeEach(() => {
  mockOnChange.mockClear();
});
//Basic rendering tests
describe('Input', () => {
  describe('Rendering', () => {
    it('renders a text input', () => {
      render(<Input value="" onChange={mockOnChange} />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('renders with the correct value', () => {
      render(<Input value="hello" onChange={mockOnChange} />);
      expect(screen.getByRole('textbox')).toHaveValue('hello');
    });

    it('renders with a placeholder when provided', () => {
      render(<Input value="" onChange={mockOnChange} placeholder="Enter text..." />);
      expect(screen.getByPlaceholderText('Enter text...')).toBeInTheDocument();
    });

    it('renders without a placeholder when not provided', () => {
      render(<Input value="" onChange={mockOnChange} />);
      expect(screen.getByRole('textbox')).not.toHaveAttribute('placeholder');
    });
  });
});