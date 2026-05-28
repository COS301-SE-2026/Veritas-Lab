import type { DropdownProps } from '@/types/components';
//still might review all of these comps that i created if we need to add styling here.
export default function Dropdown(
{
	options,
	onChange,
	defaultValue,
	disabled = false,
	className,
	optionClassName
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
				<option key={option.value} value={option.value} className={optionClassName}>
					{option.label}
				</option>
			))}
		</select>
	);
}
