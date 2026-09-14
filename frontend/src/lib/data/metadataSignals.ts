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

//AI mode names that are used in the filter for the metadata
//making use of regex:
const AI_TOOL_WORDS = [
    //OpenAI
    'gpt-?image', 'dall[\\W_]?e', 'openai', 'sora', 'chatgpt',
    //Google
    'imagen', 'gemini', 'veo', 'google ai', 'whisk', 'nano[\\W_]?banana',
    //Anthropic
    'anthropic', 'claude',
    //Adobe/Microsoft/Meta/xAI
    'firefly', 'adobe sensei', 'bing image', 'image creator', 'designer\\.microsoft',
    'copilot', 'meta ai', 'imagine with meta', '\\bemu\\b', 'grok', '\\bxai\\b', 'aurora',
    //Midjourney/Stability/open weights
    'midjourney', 'stability ?ai', 'stable ?diffusion', '\\bsdxl\\b', '\\bsd3\\b',
    'flux(\\.1|-dev|-schnell)?', 'black ?forest', 'playground ?ai', 'ideogram',
    'recraft', 'leonardo\\.?ai', 'nightcafe', 'starryai', 'artbreeder', 'krea',
    'novelai', 'dreamstudio', 'dreamshaper', 'seedream', 'seededit', 'qwen[\\W_]?image',
    'hunyuan', '\\bwan ?2', 'reve', 'higgsfield',
    //local UIs/pipelines
    'automatic1111', '\\ba1111\\b', 'comfyui', 'invokeai', 'fooocus', 'sd\\.next',
    'diffusers', 'deforum', 'animatediff', 'easy ?diffusion',
    //video/avatar/voice
    'runway', 'gen-?[234]', '\\bpika\\b', 'luma ?(ai|labs)', 'dream ?machine',
    'kling', 'hailuo', 'minimax', 'heygen', 'synthesia', 'd-?id\\b', 'elevenlabs',
    'hedra', 'captions\\.ai',
    //deepfake tooling
    'deepfake', 'faceswap', 'face ?fusion', '\\broop\\b', 'insightface', 'inswapper',
    'wav2lip', 'simswap', 'deepfacelab',
    //generic
    'generative ?ai', 'ai ?generated', 'text-?to-?image', 'text-?to-?video',
];
const AI_TOOL_PATTERN = new RegExp(`(${AI_TOOL_WORDS.join('|')})`, 'i');

//words used for the tampering filter.
const EDITOR_WORDS = [
    'photoshop', 'lightroom', 'camera ?raw', '\\bgimp\\b', 'affinity', 'paint\\.net',
    'pixlr', 'snapseed', 'facetune', 'picsart', 'canva', 'figma', 'inkscape', 'krita',
    'imagemagick', 'graphicsmagick', '\\bpillow\\b', 'skia', 'libavcodec', 'lavc', 'lavf',
    'ffmpeg', 'handbrake', 'avidemux', 'shotcut', 'premiere', 'after ?effects',
    'davinci', 'final cut', 'vegas pro', 'capcut', 'obs-?studio',
    'pypdf', 'pikepdf', 'reportlab', '\\bfpdf\\b', 'ghostscript', 'pdftk', 'itext',
    'tcpdf', 'dompdf', 'wkhtmltopdf', 'puppeteer', 'libreoffice', 'openoffice',
    'acrobat distiller', 'microsoft. word', 'quartz pdfcontext',
];
const EDITOR_PATTERN = new RegExp(`(${EDITOR_WORDS.join('|')})`, 'i');

//METADATA REGEX CHECKS TO FIND CERTAIN PATTERNS OR SIGNATURES:
//check synthetic origin declaration
const SYNTHETIC_SOURCE_PATTERN =
    /(trainedAlgorithmicMedia|compositeWithTrainedAlgorithmicMedia|algorithmicMedia|syntheticMedia)/i;
//signatures left by diffusion uis
const DIFFUSION_PARAM_PATTERN =
    /(Steps:\s*\d|Sampler:|CFG ?scale|Seed:\s*\d{4,}|Model hash|denoising_strength|"class_type"|KSampler|CheckpointLoader(Simple)?|VAEDecode|EmptyLatentImage|<lora:|sd_model|negative_prompt)/i;

const C2PA_GENERATOR_KEY = /(SoftwareAgent|Claim_?Generator|ClaimGenerator|GeneratorInfo)/i;

const DIGITAL_SOURCE_KEY = /DigitalSourceType/i;

const EDIT_ACTION_PATTERN =
    /c2pa\.(edited|color_adjustments|cropped|resized|filtered|redacted|drawing|orientation|converted|repackaged|transcoded)/i;

const CREATE_ACTION_PATTERN = /c2pa\.(created|placed)/i;

const HISTORY_KEY = /(History(Action|SoftwareAgent|When|Changed|Params|Parameters|InstanceID)|DerivedFrom)/i;

const EDITOR_NAMESPACE_KEY = /^(Photoshop|XMP-photoshop|XMP-crs|Adobe):/i;

const PROVENANCE_KEY =
    /(JUMBF:(Signature|Alg|Hash|InstanceID|Name|JUMDLabel)|c2pa\.signature|CertificateIssuer|SignatureTime)/i;

const ZERO_DATE_PATTERN = /^0{4}:0{2}:0{2}[ T]0{2}:0{2}:0{2}/;

//helper to format 
export function formatMetadataValue(value: unknown): string {
    if (value === null || value === undefined || value === '') {
        return '';
    }
    if (Array.isArray(value)) {
        return value.map((item) => formatMetadataValue(item)).join(', ');
    }
    if (typeof value === 'object') {
        try {
            return JSON.stringify(value);
        } catch {
            return String(value);
        }
    }
    return String(value);
}
//exiftool formatting
export function metadataNamespace(key: string): string {
    const index = key.indexOf(':');
    return index > 0 ? key.slice(0, index) : 'Other';
}
function keep(current: MetadataSignal | undefined, next: MetadataSignal): MetadataSignal {
    if (!current) {
        return next;
    }
    return SEVERITY_RANK[next.severity] > SEVERITY_RANK[current.severity] ? next : current;
}
function firstValue(entries: [string, string][], pattern: RegExp): string | null {
    const hit = entries.find(([key, value]) => pattern.test(key) && value !== '');
    return hit ? hit[1] : null;
}
function parseExifDate(value: string | null): number | null {
    if (!value || ZERO_DATE_PATTERN.test(value)) {
        return null;
    }
    // 2026:07:29 12:33:01+00:00 -> 2026-07-29T12:33:01+00:00
    const normalised = value
        .trim()
        .replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3')
        .replace(' ', 'T');
    const time = Date.parse(normalised);
    return Number.isNaN(time) ? null : time;
}

//analysis
function signalForEntry(key: string, value: string): MetadataSignal | null {
    if (value === '') {
        return null;
    }
    //C2PA/JUMBF claim generator naming an ai tool
    if (C2PA_GENERATOR_KEY.test(key) && AI_TOOL_PATTERN.test(value)) {
        return {
            severity: 'ai',
            label: 'AI claim',
            reason: 'The C2PA claim generator names a generative AI tool so the file declares itself as AI produced.',
        };
    }

    //digital source type declaring synthetic media
    if (DIGITAL_SOURCE_KEY.test(key) && SYNTHETIC_SOURCE_PATTERN.test(value)) {
        return {
            severity: 'ai',
            label: 'Synthetic',
            reason: 'The digital source type is declared as algorithmic/trained-algorithmic media (a code for AI generated content).',
        };
    }

    //diffusion pipeline remainders
    if (DIFFUSION_PARAM_PATTERN.test(value)) {
        return {
            severity: 'ai',
            label: 'Diffusion params',
            reason: 'This field contains diffusion generation parameters (prompt, sampler, seed or node graph) written by a local image generation UI.',
        };
    }

    //any field naming a known generative model or service
    if (AI_TOOL_PATTERN.test(value)) {
        return {
            severity: 'ai',
            label: 'AI tool',
            reason: 'The value names a known generative AI model or service.',
        };
    }

    // 5. C2PA edit actions
    if (EDIT_ACTION_PATTERN.test(value)) {
        return {
            severity: 'tamper',
            label: 'Edit action',
            reason: 'The C2PA action list records an editing operation applied after capture.',
        };
    }

    //XMP edit history/editor-only namespaces
    if (HISTORY_KEY.test(key) || EDITOR_NAMESPACE_KEY.test(key)) {
        return {
            severity: 'tamper',
            label: 'Edit history',
            reason: 'This key only exists once the file has been opened and written by an editor.',
        };
    }

    //editing/re-encoding software
    if (EDITOR_PATTERN.test(value)) {
        return {
            severity: 'tamper',
            label: 'Re-encoded',
            reason: 'The file was written by editing or re encoding software rather than straight from a capture device.',
        };
    }

    //zeroed container timestamps
    if (ZERO_DATE_PATTERN.test(value)) {
        return {
            severity: 'tamper',
            label: 'Null date',
            reason: 'The timestamp is zeroed, which is typical of scrubbed or synthetically generated containers.',
        };
    }

    //neutral provenance material
    if (PROVENANCE_KEY.test(key) || CREATE_ACTION_PATTERN.test(value)) {
        return {
            severity: 'provenance',
            label: 'Provenance',
            reason: 'Part of the embedded C2PA provenance manifest. Useful context but not suspicious on its own.',
        };
    }
    return null;
}

function buildInsights( kind: string, entries: [string, string][], signals: Record<string, MetadataSignal>,): MetadataInsight[] {
    const insights: MetadataInsight[] = [];
    const has = (pattern: RegExp) => entries.some(([key, value]) => pattern.test(key) && value !== '');
    const aiKeys = Object.entries(signals).filter(([, s]) => s.severity === 'ai');
    if (aiKeys.length > 0) {
        insights.push({
            severity: 'ai',
            title: `${aiKeys.length} AI indicator${aiKeys.length === 1 ? '' : 's'}`,
            detail: `Fields naming a generative tool or declaring synthetic origin: ${aiKeys
                .slice(0, 4)
                .map(([key]) => key)
                .join(', ')}${aiKeys.length > 4 ? '…' : ''}`,
        });
    }

    if (kind === 'image' || kind === 'video') {
        if (!has(/(^|:)(Make|Model|LensModel|LensMake|CameraModelName|AndroidModel)$/i)) {
            insights.push({
                severity: 'tamper',
                title: 'No capture device recorded',
                detail: 'There is no camera make/model. Either the file never came from a camera or the EXIF block was stripped.',
            });
        }
        if (!has(/(DateTimeOriginal|CreateDate|MediaCreateDate|TrackCreateDate)/i)) {
            insights.push({
                severity: 'tamper',
                title: 'No original capture date',
                detail: 'No DateTimeOriginal/CreateDate is present, so the capture time cannot be confirmed.',
            });
        }
    }

    const original = parseExifDate(firstValue(entries, /DateTimeOriginal/i));
    const modified = parseExifDate(firstValue(entries, /(^|:)ModifyDate$/i));
    if (original && modified && modified - original > 60_000) {
        insights.push({
            severity: 'tamper',
            title: 'Modified after capture',
            detail: 'ModifyDate is later than DateTimeOriginal so the file was rewritten after it was created.',
        });
    }

    if (kind === 'pdf' && !has(/PDF:(Creator|Author|Title)/i)) {
        insights.push({
            severity: 'tamper',
            title: 'PDF authoring fields empty',
            detail: 'Creator/Author/Title are missing which is common for scripted or sanitised PDFs.',
        });
    }

    if (entries.length > 0 && entries.every(([key]) => /^(File|Composite|SourceFile)/i.test(key))) {
        insights.push({
            severity: 'tamper',
            title: 'Only filesystem metadata present',
            detail: 'Every field comes from the filesystem layer. All embedded metadata appears to have been stripped.',
        });
    }
    return insights;
}

export function analyseMetadata( metadata: Record<string, unknown>, kind: string,): MetadataAnalysis {
    const entries: [string, string][] = Object.entries(metadata).map(([key, value]) => [
        key,
        formatMetadataValue(value),
    ]);
    const signals: Record<string, MetadataSignal> = {};
    for (const [key, value] of entries) {
        const signal = signalForEntry(key, value);
        if (signal) signals[key] = keep(signals[key], signal);
    }
    const counts: Record<SignalSeverity, number> = { ai: 0, tamper: 0, provenance: 0 };
    for (const signal of Object.values(signals)) counts[signal.severity] += 1;

    return {
        signals,
        insights: buildInsights(kind, entries, signals),
        counts,
        flaggedCount: counts.ai + counts.tamper,
    };
}