import type { ChangeEvent } from 'react';
import type { CheckBoxProps } from '@/types/components';

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
	const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
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