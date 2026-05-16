import React from 'react';

type DropdownOption = {
	label: string;
	value: string;
};

type DropdownProps = {
	options: DropdownOption[];
	onChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
	defaultValue?: string;
	disabled?: boolean;
	className?: string;
};
