import React from 'react';
import { render, screen } from '@testing-library/react';
import Text from '../../../src/components/ui/text';

//test textual rendering 
describe('Text', () => {
	it('renders the text prop', () => {
		render(<Text text="Body copy" />);
		expect(screen.getByText('Body copy')).toBeInTheDocument();
	});

	it('renders as body text by default', () => {
		render(<Text text="Body copy" />);
		expect(screen.getByText('Body copy')).toBeVisible();
	});
});