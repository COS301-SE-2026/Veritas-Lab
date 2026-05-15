import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import CheckBox from '../../../src/components/ui/checkbox';

const mockOnChange = jest.fn();

beforeEach(() => {
	mockOnChange.mockClear();
});

describe('CheckBox', () => {
    //test for rendering of checkbox
	describe('Rendering', () => {
		it('renders checkbox input', () => {
			render(<CheckBox label="Accept terms" onChange={mockOnChange} />);
			expect(screen.getByRole('checkbox')).toBeInTheDocument();
		});

		it('renders label text', () => {
			render(<CheckBox label="Accept terms" onChange={mockOnChange} />);
			expect(screen.getByLabelText('Accept terms')).toBeInTheDocument();
		});
	});

    //test to check if enabled and unchecked as default.
	describe('Default props', () => {
		it('is enabled by default', () => {
			render(<CheckBox label="Accept terms" onChange={mockOnChange} />);
			expect(screen.getByRole('checkbox')).not.toBeDisabled();
		});

		it('is unchecked by default', () => {
			render(<CheckBox label="Accept terms" onChange={mockOnChange} />);
			expect(screen.getByRole('checkbox')).not.toBeChecked();
		});
	});

    //check if when its disabled it is not clickable
	describe('Props', () => {
		it('disables checkbox when disabled={true}', () => {
			render(
				<CheckBox label="Accept terms" onChange={mockOnChange} disabled />
			);
			expect(screen.getByRole('checkbox')).toBeDisabled();
		});
        //tests to see if when we default enable it as checked it renders as such.
		it('renders as checked when checked={true}', () => {
			render(
				<CheckBox label="Accept terms" onChange={mockOnChange} checked />
			);
			expect(screen.getByRole('checkbox')).toBeChecked();
		});

		it('renders as checked when defaultChecked={true}', () => {
			render(
				<CheckBox label="Accept terms" onChange={mockOnChange} defaultChecked />
			);
			expect(screen.getByRole('checkbox')).toBeChecked();
		});
	});
    //on click interaction testing
	describe('Interactions', () => {
		it('calls onChange when clicked', () => {
			render(<CheckBox label="Accept terms" onChange={mockOnChange} />);
			fireEvent.click(screen.getByRole('checkbox'));
			expect(mockOnChange).toHaveBeenCalledTimes(1);
		});

		it('doesnt call onChange when clicked while disabled', () => {
			render(
				<CheckBox label="Accept terms" onChange={mockOnChange} disabled />
			);
			fireEvent.click(screen.getByRole('checkbox'));
			expect(mockOnChange).not.toHaveBeenCalled();
		});

        //keeps own state in DOM so the value is only read on submission. this means that its not updated onChange like if it were to be controlled.
		it('toggles when used as uncontrolled (defaultChecked)', () => {
			render(
				<CheckBox label="Accept terms" onChange={mockOnChange} defaultChecked />
			);
			const checkbox = screen.getByRole('checkbox');
			expect(checkbox).toBeChecked();
			fireEvent.click(checkbox);
			expect(checkbox).not.toBeChecked();
		});
	});
});
