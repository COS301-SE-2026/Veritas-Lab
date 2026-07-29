'use client';
import { Columns2 } from 'lucide-react';
import { EXAMPLE_BAD_METADATA, EXAMPLE_METADATA_LABELS } from '@/lib/data/referenceMetadata';
import type { MediaKind } from '@/types/workbench';

type MetadataComparisonProps = {
    mediaKind: MediaKind;
    mediaName: string;
    metadata?: Record<string, unknown> | null;
};

function formatValue(value: unknown): string
{
    if(value === null || value === undefined || value === '')
    {
        return '_';
    }
    if(Array.isArray(value))
    {
        return value.map((item) => String(item)).join(', ');
    }
    return String(value);
}

function toEntries(metadata: Record<string, unknown>): [string, string][]
{
    return Object.entries(metadata).map(([key, value]) => [key, formatValue(value)]);
}

function MetadataList({ entries }: Readonly<{ entries: [string, string][] }>)
{
    if(entries.length === 0)
    {
        return <p className="text-sm text-(--color-light)">No metadata available.</p>;
    }

    return(
        <dl className="flex flex-col gap-2 text-sm">
            {entries.map(([key, value]) => (
                <div
                    key={key}
                    className="flex flex-col gap-0.5 border-b border-(--color-light)/40 pb-2 last:border-none"
                >
                    <dt className="font-mono text-xs text-(--color-light)">{key}</dt>
                    <dd className="text-(--color-text) break-words">{value}</dd>
                </div>
            ))}
        </dl>
    );
}

export default function MetadataComparison({
    mediaKind,
    mediaName,
    metadata,
}: Readonly<MetadataComparisonProps>) {
    if(mediaKind === 'unsupported')
    {
        return (
            <div className="mt-4 rounded-2xl border border-(--color-light) p-4 text-sm text-(--color-light)">
                Metadata comparison isnt available for this file type.
            </div>
        );
    }
    const realEntries = toEntries(metadata ?? {});
    const exampleEntries = toEntries(EXAMPLE_BAD_METADATA[mediaKind]);

    return (
        <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-(--color-light) p-4">
            <div className="flex items-center gap-2">
                <Columns2 size={16} className="shrink-0 text-(--color-light)" />
                <h3 className="text-sm font-semibold text-(--color-text)">Metadata side-by-side</h3>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="flex flex-col gap-2">
                    <h4 className="text-xs font-semibold tracking-wide text-(--color-light) uppercase">
                        {mediaName}
                    </h4>
                    <MetadataList entries={realEntries} />
                </div>
                <div className="flex flex-col gap-2 md:border-l md:border-(--color-light) md:pl-4">
                    <h4 className="text-xs font-semibold tracking-wide text-(--color-light) uppercase">
                        {EXAMPLE_METADATA_LABELS[mediaKind]}
                    </h4>
                    <MetadataList entries={exampleEntries} />
                </div>
            </div>

        </div>
    );
}