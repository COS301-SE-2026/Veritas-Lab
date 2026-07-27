import { ChevronDown } from 'lucide-react';

export type Faq = {
  question: string;
  answer: string;
};

export const FAQS: Faq[] = [
  {
    question: 'What file types can I upload as evidence?',
    answer: 'PNG images and PDF documents. Anything else will be flagged as unsupported when you try to preview it in the Workbench.',
  },
  {
    question: 'Do annotations change the original file?',
    answer: 'No. Annotations live on a separate overlay layer. The underlying media is never modified, so your evidence stays forensically intact.',
  },
  {
    question: 'Why do my annotations stay in place when I resize the window?',
    answer: 'Annotation points are stored as percentages of the media\'s rendered width and height rather than as fixed pixel values, so they scale with the media.',
  },
  {
    question: 'What are the password requirements?',
    answer: 'At least 12 characters, including at least one uppercase letter, one lowercase letter, one number and one special character. You also need a valid work email address to register.',
  },
  {
    question: 'How do I get Admin access?',
    answer: 'Roles are assigned by an existing administrator from the Admin panel. Contact an admin on your team to have your role changed, you cannot elevate your own account.',
  },
  {
    question: 'Why can\'t I see the Admin option in my sidebar?',
    answer: 'The Admin link only renders for accounts with the ADMIN role. If you should have it, ask an administrator to update your role, then log out and back in so your session reflects the change.',
  },
  {
    question: 'Can an admin delete their own account?',
    answer: 'No. Admins are deliberately blocked from deleting themselves or changing their own role, so an organisation cannot accidentally lock itself out.',
  },
  {
    question: 'How do I sort or filter my cases?',
    answer: 'Use the dashboard bar. Search filters by case name, the status slider switches between All, Open and Closed and the dropdown sorts by Case Creation Date, Case Name or Case Creator.',
  },
  {
    question: 'Are my annotations saved automatically?',
    answer: 'No, click Save in the Workbench tools panel. The panel shows a saving, saved or error state so you know the result. Use Clear All to discard everything on the current evidence item.',
  },
  {
    question: 'How do I leave feedback on a case for my team?',
    answer: 'Use the case reviews panel on the case page. Comments are stored with your username and a timestamp so the investigation trail stays auditable.',
  },
];

export function filterFaqs(query: string): Faq[] {
  const q = query.trim().toLowerCase();
  if (!q) return FAQS;
  return FAQS.filter((f) => `${f.question} ${f.answer}`.toLowerCase().includes(q));
}

type FaqProps = {
  items: Faq[];
  openIndex: number | null;
  onToggle: (index: number | null) => void;
};

export default function HelpMenuFAQ({ items, openIndex, onToggle }: FaqProps) {
  return (
    <div className="divide-y divide-(--color-lightest) overflow-hidden rounded-2xl border border-(--color-lightest)">
      {items.map((f, i) => {
        const isOpen = openIndex === i;
        return (
          <div key={f.question}>
            <button
              type="button"
              onClick={() => onToggle(isOpen ? null : i)}
              aria-expanded={isOpen}
              className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left font-medium text-(--color-text) transition-colors hover:bg-(--color-lightest)"
            >
              <span>{f.question}</span>
              <ChevronDown
                size={18}
                className={`shrink-0 text-(--color-light) transition-transform ${isOpen ? 'rotate-180' : ''}`}
              />
            </button>
            {isOpen && (
              <p className="px-5 pb-4 text-sm leading-relaxed text-(--color-light)">{f.answer}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}