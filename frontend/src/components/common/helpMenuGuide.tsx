import { ScanSearch } from 'lucide-react';

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
];

export function filterGuides(query: string): Guide[] {
  const q = query.trim().toLowerCase();
  if (!q) return GUIDES;
  return GUIDES.filter((g) => `${g.title} ${g.body}`.toLowerCase().includes(q));
}

export default function HelpMenuGuide({ items }: { items: Guide[] }) {
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