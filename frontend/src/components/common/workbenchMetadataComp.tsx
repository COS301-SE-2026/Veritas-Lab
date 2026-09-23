'use client';
import { useMemo, useState } from 'react';
import { Columns2, Search, X, RefreshCw, ShieldAlert, Wrench, BadgeCheck } from 'lucide-react';
import { referenceExamples, type ExampleMediaKind, type ReferenceExample } from '@/lib/data/referenceMetadata';
import { analyseMetadata, formatMetadataValue, metadataNamespace, SEVERITY_META, SEVERITY_RANK, type MetadataAnalysis, type MetadataSignal, type SignalSeverity } from '@/lib/data/metadataSignals';
import type { MediaKindMetadataComp } from '@/types/workbench';

type MetadataComparisonProps = {
    mediaKind: MediaKindMetadataComp;
    mediaName: string;
    reportArtifacts?: Record<string, unknown> | null;
    className?: string;
};
type MetadataEntry = { key: string; value: string; signal?: MetadataSignal };
type SeverityFilter = 'all' | 'flagged' | SignalSeverity;

const SEVERITY_FILTERS: { id: SeverityFilter; label: string }[] = [
    { id: 'all', label: 'All' },
    { id: 'flagged', label: 'Flagged' },
    { id: 'ai', label: 'AI' },
    { id: 'tamper', label: 'Edits' },
    { id: 'provenance', label: 'Provenance' },
];
const SEVERITY_ICON = {
    ai: ShieldAlert,
    tamper: Wrench,
    provenance: BadgeCheck,
} as const;
const INITIAL_ROW_LIMIT = 80;

function tint(colorVar: string, percentage: number) {
    return `color-mix(in srgb, var(${colorVar}) ${percentage}%, transparent)`;
}

function extractMetadata( reportArtifacts: Record<string, unknown> | null | undefined ): Record<string, unknown> {
    const nested = reportArtifacts?.metadata;
    return nested && typeof nested === 'object' && !Array.isArray(nested) ? (nested as Record<string, unknown>) : {};
}

function buildEntries( metadata: Record<string, unknown>, analysis: MetadataAnalysis ): MetadataEntry[] {
    return Object.entries(metadata).map(([key, value]) => ({
        key,
        value: formatMetadataValue(value),
        signal: analysis.signals[key],
    }));
}

function Highlight({ text, query }: Readonly<{ text: string; query: string }>) {
    if (!query.trim()) {
        return <>{text}</>;
    }
    const escaped = query.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const parts = text.split(new RegExp(`(${escaped})`, 'ig'));
    return (
        <>
            {parts.map((part, index) =>
                part.toLowerCase() === query.trim().toLowerCase() ? (
                    <mark key={index} className="rounded-sm bg-(--color-secondary)/40 text-(--color-text)">
                        {part}
                    </mark>
                ) : (
                    <span key={index}>{part}</span>
                ),
            )}
        </>
    );
}

function SeverityChip({ severity }: Readonly<{ severity: SignalSeverity }>) {
    const meta = SEVERITY_META[severity];
    const Icon = SEVERITY_ICON[severity];
    return (
        <span
            className="inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide"
            style={{ backgroundColor: tint(meta.colorVar, 16), color: `var(${meta.colorVar})` }}
        >
            <Icon size={11} />
            {meta.label}
        </span>
    );
}

type MetadataPaneProps = {
    title: string;
    subtitle?: string;
    entries: MetadataEntry[];
    totalCount: number;
    query: string;
    action?: React.ReactNode;
};

function MetadataPane({
    title,
    subtitle,
    entries,
    totalCount,
    query,
    action,
}: Readonly<MetadataPaneProps>) {
    const [expanded, setExpanded] = useState(false);
    const visible = expanded ? entries : entries.slice(0, INITIAL_ROW_LIMIT);

    return (
        <section className="flex min-h-0 flex-col gap-3">
            <header className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                    <h4 className="truncate text-sm font-semibold text-(--color-text)">{title}</h4>
                    <p className="mt-0.5 text-xs text-(--color-light)">
                        {subtitle ? `${subtitle} · ` : ''}
                        {entries.length} of {totalCount} fields
                    </p>
                </div>
                {action}
            </header>

            {entries.length === 0 ? (
                <p className="rounded-xl bg-(--color-lightest) p-4 text-sm text-(--color-light)">
                    No fields match the current filters.
                </p>
            ) : (
                <dl className="flex min-h-0 flex-col gap-1.5 overflow-y-auto pr-1">
                    {visible.map(({ key, value, signal }) => (
                        <div
                            key={key}
                            title={signal?.reason}
                            className="rounded-xl border px-3 py-2 transition-colors"
                            style={{
                                borderColor: signal
                                    ? tint(SEVERITY_META[signal.severity].colorVar, 45)
                                    : 'color-mix(in srgb, var(--color-light) 40%, transparent)',
                                backgroundColor: signal
                                    ? tint(SEVERITY_META[signal.severity].colorVar, 7)
                                    : 'transparent',
                            }}
                        >
                            <dt className="flex items-center justify-between gap-2">
                                <span className="min-w-0 break-all font-mono text-[13px] font-semibold text-(--color-text)">
                                    <Highlight text={key} query={query} />
                                </span>
                                {signal ? <SeverityChip severity={signal.severity} /> : null}
                            </dt>
                            <dd className="mt-1 break-words text-sm leading-relaxed text-(--color-text)/85">
                                {value === '' ? (
                                    <span className="italic text-(--color-light)">empty</span>
                                ) : (
                                    <Highlight text={value} query={query} />
                                )}
                            </dd>
                            {signal ? (
                                <p
                                    className="mt-1 text-xs leading-snug"
                                    style={{ color: `var(${SEVERITY_META[signal.severity].colorVar})` }}
                                >
                                    {signal.reason}
                                </p>
                            ) : null}
                        </div>
                    ))}

                    {!expanded && entries.length > INITIAL_ROW_LIMIT ? (
                        <button
                            type="button"
                            onClick={() => setExpanded(true)}
                            className="mt-1 rounded-xl border border-(--color-light) px-3 py-2 text-sm font-semibold text-(--color-text) hover:bg-(--color-lightest)"
                        >
                            Show {entries.length - INITIAL_ROW_LIMIT} more fields
                        </button>
                    ) : null}
                </dl>
            )}
        </section>
    );
}

export default function MetadataComparison({
    mediaKind,
    mediaName,
    reportArtifacts,
    className = '',
}: Readonly<MetadataComparisonProps>) {
    const [query, setQuery] = useState('');
    const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all');
    const [namespace, setNamespace] = useState('all');
    const [hideEmpty, setHideEmpty] = useState(false);
    const [flaggedFirst, setFlaggedFirst] = useState(true);
    const [exampleIndex, setExampleIndex] = useState(0);
    const supported = mediaKind !== 'unsupported';
    const exampleKind = (supported ? mediaKind : 'image') as ExampleMediaKind;
    const examples: ReferenceExample[] = referenceExamples[exampleKind] ?? [];
    const example = examples[exampleIndex % Math.max(examples.length, 1)];
    const realMetadata = useMemo(() => extractMetadata(reportArtifacts), [reportArtifacts]);
    const realAnalysis = useMemo(
        () => analyseMetadata(realMetadata, mediaKind),
        [realMetadata, mediaKind],
    );
    const exampleAnalysis = useMemo(
        () => analyseMetadata(example?.data ?? {}, mediaKind),
        [example, mediaKind],
    );

    const realEntries = useMemo(
        () => buildEntries(realMetadata, realAnalysis),
        [realMetadata, realAnalysis],
    );
    const exampleEntries = useMemo(
        () => buildEntries(example?.data ?? {}, exampleAnalysis),
        [example, exampleAnalysis],
    );

    const namespaces = useMemo(() => {
        const set = new Set<string>();
        for (const entry of [...realEntries, ...exampleEntries]) {
            set.add(metadataNamespace(entry.key));
        }
        return [...set].sort((a, b) => a.localeCompare(b));
    }, [realEntries, exampleEntries]);

    const applyFilters = useMemo(() => {
        const needle = query.trim().toLowerCase();
        return (entries: MetadataEntry[]) => {
            const filtered = entries.filter((entry) => {
                if (hideEmpty && entry.value === '') {
                    return false;
                }
                if (namespace !== 'all' && metadataNamespace(entry.key) !== namespace) {
                    return false;
                }
                if (severityFilter === 'flagged' && !entry.signal) {
                    return false;
                }
                if ((severityFilter === 'ai' || severityFilter === 'tamper' || severityFilter === 'provenance') && entry.signal?.severity !== severityFilter) {
                    return false;
                }

                if (needle && !`${entry.key} ${entry.value}`.toLowerCase().includes(needle)) {
                    return false;
                }
                return true;
            });

            if (!flaggedFirst) return filtered;
            return [...filtered].sort(
                (a, b) =>
                    (b.signal ? SEVERITY_RANK[b.signal.severity] : 0) -
                    (a.signal ? SEVERITY_RANK[a.signal.severity] : 0),
            );
        };
    }, [query, severityFilter, namespace, hideEmpty, flaggedFirst]);

    if (!supported) {
        return (
            <div className="vl-panel mt-4 p-4 text-sm text-(--color-text-muted)">
                Metadata comparison isnt available for this file type.
            </div>
        );
    }
    const visibleReal = applyFilters(realEntries);
    const visibleExample = applyFilters(exampleEntries);
    const summary: { severity: SignalSeverity; count: number; label: string }[] = [
        { severity: 'ai', count: realAnalysis.counts.ai, label: 'AI indicators' },
        { severity: 'tamper', count: realAnalysis.counts.tamper, label: 'Edit / re-encode signs' },
        { severity: 'provenance', count: realAnalysis.counts.provenance, label: 'Provenance fields' },
    ];

    return (
        <div
            className={`flex min-h-0 flex-col gap-4 rounded-[21px] border border-(--color-light) bg-(--color-background) p-4 shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] ${className}`}
        >
            <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                    <Columns2 size={18} className="shrink-0 text-(--color-text)" />
                    <h3 className="text-lg font-bold text-(--color-text)">Metadata comparison</h3>
                </div>
                <p className="text-sm text-(--color-light)">
                    {realEntries.length} fields extracted from{' '}
                    <span className="font-semibold text-(--color-text)">{mediaName}</span>
                </p>
            </div>

            <div className="flex flex-col gap-2">
                <div className="flex flex-wrap gap-2">
                    {summary.map(({ severity, count, label }) => {
                        const meta = SEVERITY_META[severity];
                        const Icon = SEVERITY_ICON[severity];
                        return (
                            <span
                                key={severity}
                                className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-semibold"
                                style={{
                                    backgroundColor: tint(meta.colorVar, count > 0 ? 14 : 6),
                                    color: count > 0 ? `var(${meta.colorVar})` : 'var(--color-light)',
                                }}
                            >
                                <Icon size={14} />
                                {count} {label}
                            </span>
                        );
                    })}
                </div>

                {realAnalysis.insights.length > 0 ? (
                    <ul className="flex flex-col gap-1">
                        {realAnalysis.insights.map((insight) => (
                            <li
                                key={insight.title}
                                className="rounded-xl border-l-4 px-3 py-2 text-sm"
                                style={{
                                    borderColor: `var(${SEVERITY_META[insight.severity].colorVar})`,
                                    backgroundColor: tint(SEVERITY_META[insight.severity].colorVar, 6),
                                }}
                            >
                                <span className="font-semibold text-(--color-text)">{insight.title}</span>
                                <span className="text-(--color-text)/80"> - {insight.detail}</span>
                            </li>
                        ))}
                    </ul>
                ) : null}
            </div>

            <div className="flex flex-col gap-3 border-y border-(--color-light)/50 py-3">
                <div className="flex flex-wrap items-center gap-2">
                    <div className="relative min-w-[220px] flex-1">
                        <Search
                            size={16}
                            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-(--color-light)"
                        />
                        <input
                            type="search"
                            value={query}
                            onChange={(event) => setQuery(event.target.value)}
                            placeholder="Filter by key or value, e.g. Software, JUMBF, Seed"
                            aria-label="Filter metadata"
                            className="w-full rounded-full border border-(--color-light) py-2 pl-9 pr-9 text-sm text-(--color-text) outline-none focus:border-(--color-secondary)"
                        />
                        {query ? (
                            <button
                                type="button"
                                onClick={() => setQuery('')}
                                aria-label="Clear filter"
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-(--color-light) hover:text-(--color-text)"
                            >
                                <X size={16} />
                            </button>
                        ) : null}
                    </div>

                    <select
                        value={namespace}
                        onChange={(event) => setNamespace(event.target.value)}
                        aria-label="Filter by metadata group"
                        className="rounded-full border border-(--color-light) px-3 py-2 text-sm text-(--color-text) outline-none focus:border-(--color-secondary)"
                    >
                        <option value="all">All groups</option>
                        {namespaces.map((item) => (
                            <option key={item} value={item}>
                                {item}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                    <div className="flex items-center gap-1 rounded-full p-1 shadow-[inset_0_0_8px_rgba(0,0,0,0.1)]">
                        {SEVERITY_FILTERS.map(({ id, label }) => (
                            <button
                                key={id}
                                type="button"
                                onClick={() => setSeverityFilter(id)}
                                aria-pressed={severityFilter === id}
                                className={`rounded-full px-3 py-1.5 text-sm font-semibold transition-colors ${severityFilter === id
                                    ? 'bg-(--color-secondary) text-(--color-text)'
                                    : 'text-(--color-text) hover:bg-(--color-lightest)'
                                    }`}
                            >
                                {label}
                            </button>
                        ))}
                    </div>

                    <label className="ml-auto flex items-center gap-2 text-sm text-(--color-text)">
                        <input
                            type="checkbox"
                            checked={flaggedFirst}
                            onChange={(event) => setFlaggedFirst(event.target.checked)}
                            className="accent-[var(--color-secondary)]"
                        />
                        Flagged first
                    </label>
                    <label className="flex items-center gap-2 text-sm text-(--color-text)">
                        <input
                            type="checkbox"
                            checked={hideEmpty}
                            onChange={(event) => setHideEmpty(event.target.checked)}
                            className="accent-[var(--color-secondary)]"
                        />
                        Hide empty
                    </label>
                </div>
            </div>

            <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 md:grid-cols-2">
                <MetadataPane
                    title={mediaName}
                    subtitle="This evidence"
                    entries={visibleReal}
                    totalCount={realEntries.length}
                    query={query}
                />

                <div className="min-h-0 md:border-l md:border-(--color-light)/60 md:pl-4">
                    <MetadataPane
                        title={example?.label ?? 'Reference'}
                        subtitle={example?.description}
                        entries={visibleExample}
                        totalCount={exampleEntries.length}
                        query={query}
                        action={
                            examples.length > 1 ? (
                                <button
                                    type="button"
                                    onClick={() => setExampleIndex((index) => (index + 1) % examples.length)}
                                    className="inline-flex shrink-0 items-center gap-2 rounded-full border border-(--color-light) px-3 py-1.5 text-sm font-semibold text-(--color-text) hover:bg-(--color-lightest)"
                                    title="Show a different reference example"
                                >
                                    <RefreshCw size={14} />
                                    Swap example ({(exampleIndex % examples.length) + 1}/{examples.length})
                                </button>
                            ) : null
                        }
                    />
                </div>
            </div>
        </div>
    );
}