import type { ButtonProps } from '@/types/components';

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
        small: 'vl-btn-sm',
        medium: '',
        large: 'vl-btn-lg',
    };

    const variantClasses = {
        primary: 'vl-btn vl-btn-primary',
        secondary: 'vl-btn vl-btn-secondary',
        outline: 'vl-btn vl-btn-outline',
        sidebar: 'vl-btn vl-btn-icon ml-auto text-white/80',
        submit: 'vl-btn vl-btn-primary',
        sadSack: 'vl-btn vl-btn-ghost',
        light: 'vl-btn vl-btn-light',
    };

    return (
        <button onClick={onClick} disabled={disabled} type={type} className={`${sizeClasses[size]} ${variantClasses[variant]} ${className}`}>
            {children || text}
        </button>
    );
}