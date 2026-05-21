import React, { ReactNode } from 'react';

type ContainerProps = {
	children: ReactNode;
	className?: string;
};

//creation of Container comp
export default function Container({ children, className }: ContainerProps)
{
	return <div className={className}>{children}</div>;
}
//we may eventually need to add more but for now this seems to be all we need (depending on if we decide to use a global style file)