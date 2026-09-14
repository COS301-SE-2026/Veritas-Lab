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