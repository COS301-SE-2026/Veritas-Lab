import React from 'react';
import { render, screen } from '@testing-library/react';
import Heading from '../../../src/components/ui/heading';

//Basic rendering tests for now
describe('Heading', () => {
  describe('Rendering', () => {
    it('renders an h1 element', () => {
      render(<Heading text="Hello World" />);
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });

    it('renders with the correct text', () => {
      render(<Heading text="Hello World" />);
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Hello World');
    });

    it('renders only one heading', () => {
      render(<Heading text="Hello World" />);
      expect(screen.getAllByRole('heading')).toHaveLength(1);
    });
  });
});