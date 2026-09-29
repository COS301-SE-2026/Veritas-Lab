import type { MediaKind } from '@/types/workbench';
const IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'];
const VIDEO_EXTENSIONS = ['mp4'];
const PDF_EXTENSIONS = ['pdf'];

function normaliseExtension(input?: string | null): string {
    const raw = input?.trim().toLowerCase() ?? '';
    if (!raw) return '';
    if (raw.includes('/')) {
        const subtype = raw.split(';')[0].split('/').pop() ?? '';
        if (subtype && !subtype.includes('.')) {
            if (subtype === 'jpeg') {
                return 'jpeg';
            }
            return subtype;
        }
    }

    const withoutQuery = raw.split(/[?#]/)[0];
    const lastDot = withoutQuery.lastIndexOf('.');
    const candidate = lastDot >= 0 ? withoutQuery.slice(lastDot + 1) : withoutQuery;
    return candidate.replace(/[^a-z0-9]/g, '');
}
export function getMediaKind(extension?: string | null): MediaKind {
    const ext = normaliseExtension(extension);
    if (!ext) return 'unsupported';
    if (PDF_EXTENSIONS.includes(ext)) return 'pdf';
    if (IMAGE_EXTENSIONS.includes(ext)) return 'image';
    if (VIDEO_EXTENSIONS.includes(ext)) return 'video';
    return 'unsupported';
}
export function resolveMediaKind(evidence: {
    mediaExtension?: string | null;
    mediaName?: string | null;
    mediaUrl?: string | null;
}): MediaKind {
    const candidates = [evidence.mediaExtension, evidence.mediaName, evidence.mediaUrl];
    for (const candidate of candidates) {
        const kind = getMediaKind(candidate);
        if (kind !== 'unsupported') return kind;
    }
    return 'unsupported';
}