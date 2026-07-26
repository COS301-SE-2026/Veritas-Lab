import { FolderPlus, ChevronDown } from 'lucide-react';

export type Tutorial = {
  title: string;
  icon: typeof FolderPlus;
  summary: string;
  steps: string[];
};

export const TUTORIALS: Tutorial[] = [
  {
    title: 'Create your first case',
    icon: FolderPlus,
    summary: 'A case is the container for everything you investigate so evidence, annotations and reviews.',
    steps: [
      'Open the Dashboard from the sidebar.',
      'Click "New Case" to open the case creation dialog.',
      'Give the case a title and a description. Both are required.',
      'Click "Create Case". Your new case appears on the dashboard immediately.',
    ],
  }
];

export function filterTutorials(query: string): Tutorial[] {
  const q = query.trim().toLowerCase();
  if (!q) return TUTORIALS;
  return TUTORIALS.filter((t) =>
    [t.title, t.summary, t.steps.join(' ')].join(' ').toLowerCase().includes(q),
  );
}

type TutorialProps = {
  items: Tutorial[];
  openIndex: number | null;
  onToggle: (index: number | null) => void;
};

export default function HelpMenuTutorial({ items, openIndex, onToggle }: TutorialProps) {
  return (
    <div className="space-y-3">
      {items.map((t, i) => {
        const Icon = t.icon;
        const isOpen = openIndex === i;
        return (
          <div
            key={t.title}
            className="overflow-hidden rounded-2xl border border-(--color-lightest)"
          >
            <button
              type="button"
              onClick={() => onToggle(isOpen ? null : i)}
              aria-expanded={isOpen}
              className="flex w-full items-center gap-4 p-6 text-left"
            >
              <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-(--color-lightest)">
                <Icon className="size-5 text-(--color-secondary)" />
              </span>
              <span className="flex-1">
                <span className="block font-semibold text-(--color-text)">{t.title}</span>
                <span className="block text-sm text-(--color-light)">{t.summary}</span>
              </span>
              <ChevronDown
                size={18}
                className={`shrink-0 text-(--color-light) transition-transform ${isOpen ? 'rotate-180' : ''}`}
              />
            </button>

            {isOpen && (
              <div className="border-t border-(--color-lightest) px-4 py-4 pl-20">
                <ol className="list-decimal space-y-2 pl-4 text-sm text-(--color-text)">
                  {t.steps.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}