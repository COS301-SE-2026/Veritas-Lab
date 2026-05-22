import React from 'react';
import { render, screen } from '@testing-library/react';
import Container from '../../../src/components/ui/container';

//testing for rendering 
describe('Container', () => {
	it('renders children', () => {
		render(
			<Container>
				<span>Inner content</span>
			</Container>
		);
		expect(screen.getByText('Inner content')).toBeInTheDocument();
	});

	it('applies className when provided', () => {
		const { container } = render(
			<Container className="layout-width">
				<span>Inner content</span>
			</Container>
		);
		expect(container.firstChild).toHaveClass('layout-width');
	});
});
