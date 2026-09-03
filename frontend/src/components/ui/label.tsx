import type { labelProps } from '@/types/components';
//Label component for now more props may be added later

export default function Label({ children, text, htmlFor, className, variant = 'default' }: labelProps) 
{
    const variantClasses = {
        default: '',
        error: 'rounded-lg border border-[var(--color-error)] bg-[var(--color-error)]/10 px-3 py-1 text-sm text-[var(--color-error)]',
        info: 'rounded-lg border border-[var(--color-light)] bg-[var(--color-light)]/10 px-3 py-1 text-sm text-[var(--color-light)]',
        success: 'rounded-lg border border-[var(--color-secondary)] bg-[var(--color-secondary)]/10 px-3 py-2 text-sm text-[#2E9E66]'
    };

    return (
        <label htmlFor={htmlFor} className={`text-[16px] ${className || ''} ${variantClasses[variant]}`}>
            {children || text}
        </label>
    );
}