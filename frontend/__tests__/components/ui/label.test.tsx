import React from 'react';
import { render, screen } from '@testing-library/react';
import Label from '../../../src/components/ui/label';

describe('Label', () => {
    //Basic rendering tests for now
    describe('Rendering', () => {
    it('renders a label element', () => {
      render(<Label text="Username" htmlFor="username" />);
      expect(screen.getByText('Username')).toBeInTheDocument();
    });

    it('renders with the correct text', () => {
      render(<Label text="Email Address" htmlFor="email" />);
      expect(screen.getByText('Email Address')).toHaveTextContent('Email Address');
    });

    it('renders with the correct htmlFor attribute', () => {
      render(<Label text="Password" htmlFor="password" />);
      expect(screen.getByText('Password')).toHaveAttribute('for', 'password');
    });
  });
});