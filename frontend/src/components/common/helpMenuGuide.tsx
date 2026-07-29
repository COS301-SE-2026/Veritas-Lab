import {
  ScanSearch, ShieldAlert, FolderPlus, Pencil,
  ShieldCheck, Bot, FileText,
} from 'lucide-react';

export type Guide = {
  title: string;
  icon: typeof ScanSearch;
  body: string;
};

export const GUIDES: Guide[] = [
  {
    title: 'What Veritas Lab does',
    icon: ScanSearch,
    body: 'Veritas Lab is a platform for analysing and verifying the authenticity of digital media and information. Investigators and analysts upload suspicious content and run forensic analysis on it to detect manipulation, misinformation and synthetic media. It is built in partnership with Naked Insurance.',
  },
  {
    title: 'Core capabilities',
    icon: ShieldAlert,
    body: 'AI-powered analysis surfaces insights about media content. Content review gives you tools to assess material properly. Tamper detection identifies manipulated media. Deepfake detection flags AI-generated content.',
  },
  {
    title: 'How a case is structured',
    icon: FolderPlus,
    body: 'A case has a title, a description, a creator and a status of Open or Closed. Inside a case you attach evidence items and each evidence item carries its own annotations. Case reviews are comments attached to the case as a whole, recorded against a username and timestamp.',
  },
  {
    title: 'Annotation model',
    icon: Pencil,
    body: 'There are two kinds of annotation. A shape is a freehand path used to circle or outline a suspicious region. A note is a text comment pinned to a single point. Both record the page they belong to, which matters for multi-page PDFs. Coordinates are stored as percentages of the rendered media rather than raw pixels, so annotations stay correctly positioned across screen sizes and window resizes.',
  },
  {
    title: 'Roles and permissions',
    icon: ShieldCheck,
    body: 'There are three roles. USER is the baseline account. INVESTIGATOR works on cases and evidence. ADMIN additionally sees the Admin panel and can manage user accounts and roles. Your role is carried in your session token and determines what appears in your sidebar.',
  },
  {
    title: 'Accounts and passwords',
    icon: Bot,
    body: 'Register with a valid work email address. Passwords must be at least 12 characters and must include an uppercase letter, a lowercase letter, a number and a special character. Sessions are managed with JWTs, and you can end yours at any time using Log Out at the bottom of the sidebar.',
  },
  {
    title: 'Supported file formats',
    icon: FileText,
    body: 'Evidence uploads currently accept PNG images and PDF documents. PDFs render page by page and annotations are tracked per page. Any other format will be shown as unsupported in the workbench canvas.',
  },
];

export function filterGuides(query: string): Guide[] {
  const q = query.trim().toLowerCase();
  if (!q) return GUIDES;
  return GUIDES.filter((g) => `${g.title} ${g.body}`.toLowerCase().includes(q));
}

export default function HelpMenuGuide({ items }: Readonly<{ items: Guide[] }>) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {items.map((g) => {
        const Icon = g.icon;
        return (
          <div
            key={g.title}
            className="rounded-2xl bg-(--color-lightest) p-5 transition-shadow hover:shadow-md"
          >
            <span className="flex size-12 items-center justify-center rounded-xl bg-(--color-background)">
              <Icon className="size-6 text-(--color-secondary)" />
            </span>
            <h2 className="mt-4 text-lg font-bold text-(--color-text)">{g.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-(--color-text)">{g.body}</p>
          </div>
        );
      })}
    </div>
  );
}