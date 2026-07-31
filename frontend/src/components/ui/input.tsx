import type { InputProps } from '@/types/components';

export default function Input({ placeholder, value, onChange, id, type, className, required }: InputProps) {
    const inputClasses = {
        primary: 'w-full rounded-full border border-[var(--color-light)] bg-white px-4 py-2.5 text-[var(--color-text)] ' +
            'placeholder:text-[var(--color-light)] transition-colors duration-150 ' +
            'hover:border-[var(--color-dark)] ' +
            'focus:border-[var(--color-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-secondary)]/40 ' +
            'disabled:cursor-not-allowed disabled:opacity-60'
    }
        
    

    return (
        <input
            id={id}
            type={type || "text"}
            placeholder={placeholder}
            className={className || inputClasses.primary}
            value={value}
            onChange={onChange ? (e) => onChange(e.target.value) : undefined}
            required={required}
        />
    );
}