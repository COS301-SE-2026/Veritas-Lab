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

	return (
		<label className={className}>
			<input
				type="checkbox"
				onChange={onChange}
				disabled={disabled}
				checked={isControlled ? checked : undefined}
				defaultChecked={!isControlled ? defaultChecked : undefined}
			/>
			{label}
		</label>
	);
}