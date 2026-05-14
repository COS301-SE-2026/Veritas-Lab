import React, { ReactNode } from 'react';

type ButtonProps = {
    text: string;
    onClick: () => void;
    disabled?: boolean;
    type?: 'button' | 'submit' | 'reset';
    variant?: 'primary' | 'secondary' | 'outline';
    size?: 'small' | 'medium' | 'large';
};

export default function Button({ 
    text,
    onClick,
    disabled = false,
    type = 'button',
    variant = 'primary',
    size = 'medium'
 }: ButtonProps) {

    const sizeClasses = {
        small: '',
        medium: '',
        large: ''
    };

    const variantClasses = {
        primary: '',
        secondary: '',
        outline: ''
    };

    return (
        <button onClick={onClick} disabled={disabled} type={type} className={`${sizeClasses[size]} ${variantClasses[variant]}`}>
            {text}
        </button>
    );
}