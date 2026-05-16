//Label component for now more props may be added later
type labelProps = {
    text: string;
    htmlFor: string;
    className?: string;
};

export default function Label({ text, htmlFor, className }: labelProps) {
    return (
        <label htmlFor={htmlFor} className={`text-[16px] ${className || ''}`}>
            {text}
        </label>
    );
}