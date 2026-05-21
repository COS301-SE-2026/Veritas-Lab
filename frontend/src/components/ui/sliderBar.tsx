'use client';
import { useState } from 'react';

type SliderBarProps<T extends string = string> = {
    filters: ReadonlyArray<T>;
    defaultFilter?: T;
    onChange?: (filter: T) => void;
    className?: string;
};

export default function SliderBar<T extends string>({ filters, defaultFilter, onChange, className }: SliderBarProps<T>) {
    const [active, setActive] = useState<T>(defaultFilter ?? filters[0]);

    const handleClick = (filter: T) => {
        setActive(filter);
        onChange?.(filter);
    };

    return (
        <div className={`flex items-center shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] rounded-full w-full p-1 ${className ?? ''}`}>
            {filters.map((filter) => (
                <button
                    key={filter}
                    onClick={() => handleClick(filter)}
                    className={`flex-1 py-3 rounded-full text-sm font-semibold transition-colors duration-200
                        ${active === filter
                            ? 'text-[var(--color-text)] bg-[var(--color-secondary)]'
                            : 'text-[var(--color-text)] hover:bg-gray-100'
                        }`}
                >
                    {filter}
                </button>
            ))}
        </div>
    );
}