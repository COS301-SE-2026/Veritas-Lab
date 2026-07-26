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
    <div className="divide-y divide-(--color-lightest) overflow-hidden rounded-xl">
      {items.map((f, i) => {
        const isOpen = openIndex === i;
        return (
          <div key={f.question}>
            <button
              type="button"
              onClick={() => onToggle(isOpen ? null : i)}
              aria-expanded={isOpen}
              className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left font-large text-(--color-text) transition-colors hover:bg-(--color-lightest)"
            >
              <span>{f.question}</span>
              <ChevronDown
                size={18}
                className={`shrink-0 text-(--color-light) transition-transform ${isOpen ? 'rotate-180' : ''}`}
              />
            </button>
            {isOpen && (
              <p className="px-3 pb-4 text-sm leading-relaxed text-(--color-light)">{f.answer}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}