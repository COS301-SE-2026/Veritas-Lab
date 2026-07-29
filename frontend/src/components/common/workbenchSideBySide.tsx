'use client';
import { Columns2 } from 'lucide-react';
import {
    badExampleData,
    exampleLabels,
} from '@/lib/data/referenceMetadata';
import type { MediaKind } from '@/types/workbench';

type MetadataComparisonProps = {
    mediaKind: MediaKind;
    mediaName: string;
    reportArtifacts?: Record<string, unknown> | null;
};

type MetadataEntry = [string, string];
const PNG_TRIAGE_KIND: MediaKind = 'image';
const JUMBF_PRIORITY_PATTERN = /(SoftwareAgent|Claim_Generator)/i;
const MAX_METADATA_ENTRIES = 25;
function isJumbfKey(key: string): boolean {
    return key.startsWith('JUMBF:');
}

function isPriorityJumbfKey(key: string): boolean {
    return isJumbfKey(key) && JUMBF_PRIORITY_PATTERN.test(key);
}

function isPngTriageKind(kind: MediaKind): boolean {
    return kind === PNG_TRIAGE_KIND;
}

function formatValue(value: unknown): string {
    if (value === null || value === undefined || value === '') {
        return '_';
    }
    if (Array.isArray(value)) {
        return value.map(String).join(', ');
    }
    return String(value);
}

function toEntries(metadata: Record<string, unknown>): MetadataEntry[] {
    return Object.entries(metadata).map(([key, value]) => [key, formatValue(value)]);
}

//png specific metadata extraction.
function selectPngMetadataEntries(metadata: Record<string, unknown>): MetadataEntry[] {
    const allEntries = Object.entries(metadata);
    const priorityEntries = allEntries.filter(([key]) => isPriorityJumbfKey(key));
    if (priorityEntries.length === 0) {
        return allEntries.map(([key, value]) => [key, formatValue(value)] as MetadataEntry);
    }
    const nonJumbfEntries = allEntries.filter(([key]) => !isJumbfKey(key));
    return [...priorityEntries, ...nonJumbfEntries]
        .slice(0, MAX_METADATA_ENTRIES)
        .map(([key, value]) => [key, formatValue(value)] as MetadataEntry);
}

function buildEntries(mediaKind: MediaKind, metadata: Record<string, unknown>): MetadataEntry[] {
    if (isPngTriageKind(mediaKind)) {
        return selectPngMetadataEntries(metadata);
    }
    return toEntries(metadata);
}

/** Pulls the nested `metadata` object out of a CaseEvidence.reportArtifacts envelope. */
function extractMetadata(reportArtifacts: Record<string, unknown> | null | undefined): Record<string, unknown> {
    const nested = reportArtifacts?.metadata;
    return nested && typeof nested === 'object' && !Array.isArray(nested)
        ? (nested as Record<string, unknown>)
        : {};
}

function MetadataList({ entries }: Readonly<{ entries: MetadataEntry[] }>) {
    if (entries.length === 0) {
        return <p className="text-sm text-(--color-light)">No metadata available.</p>;
    }

    return (
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
    reportArtifacts,
}: Readonly<MetadataComparisonProps>) {
    if (mediaKind === 'unsupported') {
        return (
            <div className="mt-4 rounded-2xl border border-(--color-light) p-4 text-sm text-(--color-light)">
                Metadata comparison isnt available for this file type.
            </div>
        );
    }
    const realMetadata = extractMetadata(reportArtifacts);
    const realEntries = buildEntries(mediaKind, realMetadata);
    const exampleEntries = buildEntries(mediaKind, badExampleData[mediaKind]);

    return (
        <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-(--color-light) p-4">
            <div className="flex items-center gap-2">
                <Columns2 size={16} className="shrink-0 text-(--color-light)" />
                <h3 className="text-sm font-semibold text-(--color-text)">
                    Metadata side-by-side
                </h3>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="flex flex-col gap-2">
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-(--color-light)">
                        {mediaName}
                    </h4>
                    <MetadataList entries={realEntries} />
                </div>

                <div className="flex flex-col gap-2 md:border-l md:border-(--color-light) md:pl-4">
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-(--color-light)">
                        {exampleLabels[mediaKind]}
                    </h4>
                    <MetadataList entries={exampleEntries} />
                </div>
            </div>
        </div>
    );
}