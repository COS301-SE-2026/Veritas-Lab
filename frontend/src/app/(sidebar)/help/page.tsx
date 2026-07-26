import { useState, useMemo } from 'react';
import Link from 'next/link';
import {
  HelpCircle, GraduationCap, BookOpen, MessageCircleQuestion,
  Search, Mail,
} from 'lucide-react';
import HelpMenuTutorial, { filterTutorials } from '@/components/common/helpMenuTutorial';
import HelpMenuGuide, { filterGuides } from '@/components/common/helpMenuGuide';
import HelpMenuFAQ, { filterFaqs } from '@/components/common/helpMenuFAQ';

type Tab = 'tutorials' | 'guides' | 'faqs';

const TABS: { id: Tab; label: string; icon: typeof GraduationCap }[] = [
  { id: 'tutorials', label: 'Tutorials', icon: GraduationCap },
  { id: 'guides', label: 'Guides & Docs', icon: BookOpen },
  { id: 'faqs', label: 'FAQs', icon: MessageCircleQuestion },
];

const SUPPORT_EMAIL = 'support.deltatech@gmail.com';

export default function HelpPage() {
  const [tab, setTab] = useState<Tab>('tutorials');
  const [search, setSearch] = useState('');
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [openTutorial, setOpenTutorial] = useState<number | null>(0);

  const q = search.trim().toLowerCase();

  const tutorials = useMemo(() => filterTutorials(search), [search]);
  const guides = useMemo(() => filterGuides(search), [search]);
  const faqs = useMemo(() => filterFaqs(search), [search]);

  const counts: Record<Tab, number> = {
    tutorials: tutorials.length,
    guides: guides.length,
    faqs: faqs.length,
  };

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8">
      {/* Header which housees the search */}
      <header className="mb-8">
        <div className="flex items-center gap-3">
          <span className="flex size-12 items-center justify-center rounded-2xl bg-(--color-lightest)">
            <HelpCircle className="size-7 text-(--color-secondary)" />
          </span>
          <div>
            <h1 className="text-3xl font-bold text-(--color-text)">Help Menu</h1>
            <p className="text-(--color-light)">
              Tutorials, guides and answers for working in Veritas Lab.
            </p>
          </div>
        </div>

        {/* Search, pretty obvious */}
        <div className="relative mt-6">
          <Search
            size={18}
            className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-(--color-light)"
          />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search help articles, guides and FAQs..."
            aria-label="Search help"
            className="w-full rounded-full py-3 pl-12 pr-4 text-(--color-text) shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] focus:outline-none focus:ring-2 focus:ring-(--color-secondary)"
          />
        </div>
      </header>

      {/* Tabs to navigate between different help sections */}
      <nav className="mb-6 flex flex-wrap gap-2" aria-label="Help sections">
        {TABS.map(({ id, label, icon: Icon }) => {
          const active = tab === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => setTab(id)}
              aria-current={active ? 'page' : undefined}
              className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                active
                  ? 'bg-(--color-secondary) text-(--color-text)'
                  : 'text-(--color-text) hover:bg-(--color-lightest)'
              }`}
            >
              <Icon size={16} />
              {label}
              {q && (
                <span className="rounded-full bg-black/10 px-1.5 text-xs">{counts[id]}</span>
              )}
            </button>
          );
        })}
      </nav>

      {counts[tab] === 0 && <Empty query={search} />}

      {tab === 'tutorials' && (
        <HelpMenuTutorial
          items={tutorials}
          openIndex={openTutorial}
          onToggle={setOpenTutorial}
        />
      )}

      {tab === 'guides' && <HelpMenuGuide items={guides} />}

      {tab === 'faqs' && (
        <HelpMenuFAQ items={faqs} openIndex={openFaq} onToggle={setOpenFaq} />
      )}

      {/* Footer which includes the extra help options */}
      <footer className="mt-10 flex flex-col items-start gap-4 rounded-2xl bg-(--color-primary) p-6 text-white sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-bold">Still need help?</h2>
          <p className="text-sm text-white/70">
            Reach the Delta Tech team and we&apos;ll get back to you.
          </p>
        </div>
        <a
          href={`mailto:${SUPPORT_EMAIL}`}
          className="flex items-center gap-2 rounded-full bg-(--color-secondary) px-5 py-2.5 font-semibold text-(--color-text) transition-colors hover:bg-[#2E9E66]"
        >
          <Mail size={18} />
          Contact support
        </a>
      </footer>

      <p className="mt-6 text-center text-sm text-(--color-light)">
        Looking for your cases?{' '}
        <Link href="/dashboard" className="font-medium text-(--color-text) underline">
          Back to Dashboard
        </Link>
      </p>
    </div>
  );
}
// The empty search result
function Empty({ query }: { query: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-(--color-light) p-10 text-center">
      <Search className="mx-auto size-8 text-(--color-light)" />
      <p className="mt-3 font-medium text-(--color-text)">
        No results for &ldquo;{query}&rdquo;
      </p>
      <p className="text-sm text-(--color-light)">
        Try a different term, or check another section.
      </p>
    </div>
  );
}