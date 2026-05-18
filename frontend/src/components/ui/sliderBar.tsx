'use client';
import { useState } from 'react';

type SliderBarProps = {
    filters: string[];
    defaultFilter?: string;
    onChange?: (filter: string) => void;
    className?: string;
};

export default function SliderBar({ filters, defaultFilter, onChange, className }: SliderBarProps) {
    const [active, setActive] = useState(defaultFilter ?? filters[0]);

    const handleClick = (filter: string) => {
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
                            ? 'text-white bg-[var(--color-primary)]'
                            : 'text-[var(--color-text)] hover:bg-gray-100'
                        }`}
                >
                    {filter}
                </button>
            ))}
        </div>
    );
}