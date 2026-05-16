import React from 'react';

type CheckBoxProps = {
	label: string;
	onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
	checked?: boolean;
	defaultChecked?: boolean;
	disabled?: boolean;
	className?: string;
};
