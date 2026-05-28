import type { InputProps } from '@/types/components';

export default function Input({ placeholder, value, onChange, id, type, className, required }: InputProps) {
    return (
        <input
            id={id}
            type={type || "text"}
            placeholder={placeholder}
            className={className}
            value={value}
            onChange={onChange ? (e) => onChange(e.target.value) : undefined}
            required={required}
        />
    );
}