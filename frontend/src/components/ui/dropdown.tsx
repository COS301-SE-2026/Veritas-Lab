import React from 'react';

type DropdownOption = {
	label: string;
	value: string;
};

type DropdownProps = {
	options: DropdownOption[];
	onChange?: (event: React.ChangeEvent<HTMLSelectElement>) => void;
	defaultValue?: string;
	disabled?: boolean;
	className?: string;
};
//still might review all of these comps that i created if we need to add styling here.
export default function Dropdown(
{
	options,
	onChange,
	defaultValue,
	disabled = false,
	className
}: DropdownProps)
{
	return (
		<select
			onChange={onChange}
			defaultValue={defaultValue}
			disabled={disabled}
			className={className}
		>
			{options.map((option) => (
				<option key={option.value} value={option.value}>
					{option.label}
				</option>
			))}
		</select>
	);
}
