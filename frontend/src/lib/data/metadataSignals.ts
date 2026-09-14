export type SignalSeverity = 'ai' | 'tamper' | 'provenance';
export type MetadataSignal = {
    severity: SignalSeverity;
    label: string;
    reason: string;
};
export type MetadataInsight = {
    severity: SignalSeverity;
    title: string;
    detail: string;
};
export type MetadataAnalysis = {
    signals: Record<string, MetadataSignal>;
    insights: MetadataInsight[];
    counts: Record<SignalSeverity, number>;
    flaggedCount: number;
};

export const SEVERITY_RANK: Record<SignalSeverity, number> = {
    ai: 3,
    tamper: 2,
    provenance: 1, //these can be adjusted. just preliminary
};

export const SEVERITY_META: Record<
    SignalSeverity,
    { label: string; colorVar: string }
> = {
    ai: { label: 'AI', colorVar: '--color-error' },
    tamper: { label: 'Edited', colorVar: '--color-warning' },
    provenance: { label: 'Provenance', colorVar: '--color-info' }, //uses our existing style
};