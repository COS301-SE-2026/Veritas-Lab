type InputProps = {
    placeholder?: string;
    value?: string;
    onChange?: (value: string) => void;
    id?: string;
    type?: string;
    className?: string;
};

export default function Input({ placeholder, value, onChange, id, type, className }: InputProps) {
    return (
        <input
            id={id}
            type={type || "text"}
            placeholder={placeholder}
            className={className}
            value={value}
            onChange={onChange ? (e) => onChange(e.target.value) : undefined}
        />
    );
}