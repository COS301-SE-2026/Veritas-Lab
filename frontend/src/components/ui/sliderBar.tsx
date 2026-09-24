'use client';
import { useState } from 'react';
import type { SliderBarProps } from '@/types/components';

export default function SliderBar<T extends string>({ filters, defaultFilter, onChange, className }: SliderBarProps<T>) {
    const [active, setActive] = useState<T>(defaultFilter ?? filters[0]);

    const handleClick = (filter: T) => {
        setActive(filter);
        onChange?.(filter);
    };

    return (
        <div
            className={`flex items-center gap-1 rounded-full border border-(--color-line) bg-(--color-surface-sunken) p-1 w-full ${className ?? ''}`}
        >
            {filters.map((filter) => {
                const isActive = active === filter;
                return (
                    <button
                        key={filter}
                        onClick={() => handleClick(filter)}
                        aria-pressed={isActive}
                        className={`flex-1 rounded-full py-2.5 text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--b-500)_45%,transparent)]
                            ${isActive
                                ? 'bg-(--color-secondary) text-(--color-text) shadow-[0_2px_8px_-2px_color-mix(in_srgb,var(--b-600)_60%,transparent)]'
                                : 'text-(--color-text-muted) hover:bg-(--color-surface) hover:text-(--color-text-strong)'
                            }`}
                    >
                        {filter}
                    </button>
                );
            })}
        </div>
    );
}