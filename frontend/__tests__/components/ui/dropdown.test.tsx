import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Dropdown from '../../../src/components/ui/dropdown';

const mockOnChange = jest.fn();

//mock the test with just two options as that is enough to test functionality.
const options = [
	{ label: 'Option one', value: 'one' },
	{ label: 'Option two', value: 'two' }
];

beforeEach(() => {
	mockOnChange.mockClear();
});
//redering test
describe('Dropdown', () => {
	it('renders a select input', () => {
		render(<Dropdown options={options} onChange={mockOnChange} />);
		expect(screen.getByRole('combobox')).toBeInTheDocument();
	});

	it('renders the provided options', () => {
		render(<Dropdown options={options} onChange={mockOnChange} />);
		expect(screen.getByRole('option', { name: 'Option one' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Option two' })).toBeInTheDocument();
	});

	it('calls onChange when selection changes', () => {
		render(<Dropdown options={options} onChange={mockOnChange} />);
		fireEvent.change(screen.getByRole('combobox'), { target: { value: 'two' } });
		expect(mockOnChange).toHaveBeenCalledTimes(1);
	});
    //test that if provided a default it works as the selected option
	it('respects defaultValue when provided', () => {
		render(
			<Dropdown options={options} onChange={mockOnChange} defaultValue="two" />
		);
		expect(screen.getByRole('combobox')).toHaveValue('two');
	});

	it('disables the dropdown when disabled={true}', () => {
		render(
			<Dropdown options={options} onChange={mockOnChange} disabled />
		);
		expect(screen.getByRole('combobox')).toBeDisabled();
	});
});
