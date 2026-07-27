import {
  FolderPlus, UploadCloud, Pencil, LayoutDashboard,
  ClipboardCheck, UserStar, ChevronDown,
} from 'lucide-react';

export type Tutorial = {
  title: string;
  icon: typeof FolderPlus;
  summary: string;
  steps: string[];
  note?: string;
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
  },
  {
    title: 'Upload evidence to a case',
    icon: UploadCloud,
    summary: 'Evidence is the media you want to verify. Each item gets its own workbench.',
    steps: [
      'Open a case from the Dashboard.',
      'Click the upload area to browse for a file.',
      'Select a PNG image or a PDF document, currently these are the supported formats.',
      'Submit the upload. The evidence appears as a card on the case page.',
    ],
    note: 'Only PNG and PDF are supported right now.',
  },
  {
    title: 'Annotate evidence in the Workbench',
    icon: Pencil,
    summary: 'The Workbench is where you mark up media so you can circle tampered regions and pin notes.',
    steps: [
      'From a case page, click an evidence item to open the Workbench.',
      'In the Tools panel on the right, select "Annotations".',
      'Pick a tool: Select to pick existing annotations, Draw to sketch freehand shapes, Comment to pin a text note.',
      'Draw over the region you want to flag, or click a point and type your note.',
      'Review your marks in the annotation list, remove any you do not want, then click Save.',
    ],
    note: 'Annotations sit on an overlay and never modify the original media. Positions are stored as percentages, so your marks stay aligned when the window is resized.',
  },
  {
    title: 'Find and organise cases',
    icon: LayoutDashboard,
    summary: 'The dashboard bar lets you narrow a long case list down quickly.',
    steps: [
      'Use the search box to filter cases by name.',
      'Use the status slider to switch between All, Open and Closed cases.',
      'Use the sort dropdown to order by Case Creation Date, Case Name or Case Creator.',
    ],
  },
  {
    title: 'Discuss a case with your team',
    icon: ClipboardCheck,
    summary: 'Case reviews keep the investigation trail in one place.',
    steps: [
      'Open the case you want to discuss.',
      'Find the case reviews panel.',
      'Write your comment and submit it.',
      'Your comment is recorded with your username and a timestamp for everyone on the case.',
    ],
  },
  {
    title: 'Manage users (Admins only)',
    icon: UserStar,
    summary: 'Admins control who has access and what role they hold.',
    steps: [
      'Click "Admin" in the sidebar, this only appears if your account has the ADMIN role.',
      'Search for a user by name in the users panel.',
      'Change their role, or remove the account if access should be revoked.',
    ],
    note: 'As a safety measure, an admin cannot delete their own account or change their own role.',
  },
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
              className="flex w-full items-center gap-4 p-4 text-left transition-colors hover:bg-(--color-lightest)"
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
                <ol className="list-decimal space-y-2 pl-4 text-sm text-(--color-text) marker:font-semibold marker:text-(--color-secondary)">
                  {t.steps.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ol>
                {t.note && (
                  <p className="mt-4 rounded-xl bg-(--color-lightest) p-3 text-sm text-(--color-text)">
                    <strong className="font-semibold">Note: </strong>
                    {t.note}
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}