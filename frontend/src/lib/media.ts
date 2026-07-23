import type { MediaKind } from '@/types/workbench';

// Just png for now since I believe that our only image type for now
const IMAGE_EXTENSION = 'png';

// Determines how a piece of media should be previewed from its file extension
export function getMediaKind(extension?: string | null): MediaKind {
    const ext = extension?.trim().replace(/^\./, '').toLowerCase() ?? '';

    if (ext === 'pdf') return 'pdf';
    if (ext === IMAGE_EXTENSION) return 'image';
    return 'unsupported';
}