import type { labelProps } from '@/types/components';
//Label component for now more props may be added later

export default function Label({ text, htmlFor, className }: labelProps) {
    return (
        <label htmlFor={htmlFor} className={`text-[16px] ${className || ''}`}>
            {text}
        </label>
    );
}