import { isValid, parseISO } from 'date-fns';

export function extractMetadata( reportArtifacts: Record<string, unknown> | null | undefined ) : Record<string, unknown> {
    const metadata = reportArtifacts?.metadata;
    if(metadata && typeof metadata === 'object') {
        return metadata as Record<string, unknown>
    }
    return {}
}

//finds the metadata tag that matches the common possible ways of labeling the creation tag
function pick(meta: Record<string, unknown>, keys: string[]): [string, string] | undefined {
    for (const key of keys) {
        for (const [label, record] of Object.entries(meta)) {
            let val = label.split(':').pop();
            if (!val) {val = label}
            if (val.toLocaleLowerCase() === key && typeof record === 'string' && record.trim()) {
                return [label, record.trim()];
            }
        }
    }
    return undefined;
}

const dates = ['subsecdatetimeoriginal', 'datetimeoriginal', 'createdate', 'mediacreatedate', 'creationdate'];
const offsets = ['offsettimeoriginal', 'offsettime'];
const zone = /(Z|[+-]\d{2}:?\d{2})$/i;

//returns the date after doing a bit more cleaning
export function getCapturedAt(reportArtifacts: Record<string, unknown> | null | undefined): number | null {
    const meta = extractMetadata(reportArtifacts);
    const [key, raw] = pick(meta, dates) ?? [];
    if (!raw || raw.startsWith('0000')) return null;

    let iso = raw.replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3');
    if (!zone.test(iso)) {
        iso += pick(meta, offsets)?.[1] ?? (key?.startsWith('QuickTime:') ? 'Z' : '');
    }

    const date = parseISO(iso);
    return isValid(date) ? date.getTime() : null;
}