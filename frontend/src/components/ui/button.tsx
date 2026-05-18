import React from 'react';

type ButtonProps = {
    children?: React.ReactNode;
    text?: string;
    onClick?: () => void;
    disabled?: boolean;
    type?: 'button' | 'submit' | 'reset';
    variant?: 'primary' | 'secondary' | 'outline' | 'sidebar' | 'submit' | 'sadSack';
    size?: 'small' | 'medium' | 'large';
    className?: string;
};

export default function Button({ 
    children,
    text,
    onClick,
    disabled = false,
    type = 'button',
    variant = 'primary',
    size = 'medium',
    className = '',
 }: ButtonProps) {

    const sizeClasses = {
        small: '',
        medium: '',
        large: '',
    };

    const variantClasses = {
        primary: '',
        secondary: '',
        outline: 'py-2 px-4 border-[var(--color-primary)] border-1 text-[var(--color-primary)] hover:bg-[#231F20] rounded-full hover:text-white transition-colors',
        sidebar: 'p-2 rounded-md hover:bg-[#231F20] transition-colors ml-auto',
        submit: 'bg-[var(--color-primary)] text-white font-medium py-2 px-4 rounded-full hover:bg-[#2E9E66] transition-colors font-semibold',
        sadSack: 'py-2 px-4 text-[var(--color-text)] hover:text-[var(--color-primary)] rounded-full',
    };

    return (
        <button onClick={onClick} disabled={disabled} type={type} className={`${sizeClasses[size]} ${variantClasses[variant]} ${className}`}>
            {children || text}
        </button>
    );
}