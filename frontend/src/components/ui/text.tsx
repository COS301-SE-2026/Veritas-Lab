import React from 'react';

type TextProps = {
	text: string;
	className?: string;
};
//there is basically no other functionality to setup other than to add styling if we agree on that.
export default function Text({ text, className }: TextProps)
{
	return <p className={className}>{text}</p>;
}
