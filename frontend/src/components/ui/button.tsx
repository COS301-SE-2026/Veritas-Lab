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
        small: '',
        medium: '',
        large: '',
    };

    const variantClasses = {
        primary: '',
        secondary: '',
        outline: 'py-2 px-4 border-[var(--color-primary)] border-1 text-[var(--color-primary)] hover:bg-(--color-dark) rounded-full hover:text-white transition-colors',
        sidebar: 'p-2 rounded-md hover:bg-(--color-dark) transition-colors ml-auto',
        submit: 'bg-[var(--color-secondary)] text-(--color-text) font-medium py-2 px-4 rounded-full hover:bg-[#2E9E66] transition-colors font-semibold',
        sadSack: 'py-2 px-4 text-[var(--color-text)] hover:text-[var(--color-primary)] rounded-full',
    };

    return (
        <button onClick={onClick} disabled={disabled} type={type} className={`${sizeClasses[size]} ${variantClasses[variant]} ${className}`}>
            {children || text}
        </button>
    );
}