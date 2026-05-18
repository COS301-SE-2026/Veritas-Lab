import React from 'react';

type CheckBoxProps = {
	label: string;
	onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
	checked?: boolean;
	defaultChecked?: boolean;
	disabled?: boolean;
	className?: string;
};

export default function CheckBox(
{
	label,
	onChange,
	checked,
	defaultChecked,
	disabled = false,
	className
}: CheckBoxProps)
{
	const isControlled = typeof checked === 'boolean';
	//handles a missed error
	const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
		if(disabled)
		{
			return;
		}

		onChange(event);
	};

	return (
		<label className={className}>
			<input
				type="checkbox"
				onChange={handleChange}
				disabled={disabled}
				checked={isControlled ? checked : undefined}
				defaultChecked={!isControlled ? defaultChecked : undefined}
			/>
			{label}
		</label>
	);
}