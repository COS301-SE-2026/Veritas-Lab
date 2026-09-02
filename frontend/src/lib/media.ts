import type { MediaKind } from '@/types/workbench';

// Just png for now since I believe that our only image type for now
const IMAGE_EXTENSION = ['png','jpeg','jpg'];
const VIDEO_EXTENSION = ['mp4'];

// Determines how a piece of media should be previewed from its file extension
export function getMediaKind(extension?: string | null): MediaKind {
    const ext = extension?.trim().replace(/^\./, '').toLowerCase() ?? '';

    if (ext === 'pdf') return 'pdf';
    if (IMAGE_EXTENSION.includes(ext)) return 'image';
    if (VIDEO_EXTENSION.includes(ext)) return 'video';
    return 'unsupported';
}