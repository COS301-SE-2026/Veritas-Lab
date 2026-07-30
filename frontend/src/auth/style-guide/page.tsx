'use client';

import {useEffect, useRef, useState} from 'react';
import type { ReactNode } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import {
  Palette, Type, Shapes, Boxes, LayoutGrid, Accessibility, MessageSquare, History,
  Home, HelpCircle, LogOut, UserStar, ChevronLeft, Menu, Search, Mail,
} from 'lucide-react';
import Button from '@/components/ui/button';
import Input from '@/components/ui/input';
import Modal from '@/components/ui/modal';
import CaseCard from '@/components/common/caseCard';
import EvidenceCard from '@/components/common/evidenceCard';

function Reveal({ children, className = '' }: Readonly<{ children: ReactNode; className?: string }>) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
        ([entry]) => {
            if (entry.isIntersecting) {
                setVisible(true);
                observer.disconnect();
            }
        },
        { threshold: 0.15 },
    );
    observer.observe(node);
    return () => observer.disconnect();
    }, []);

    return (
        <div
            ref={ref}
            className={`transition-all-duration-700 ease-out ${visible ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'} ${className}`}
        >
            {children}
        </div>
    );
}

function GapNote({ children }: Readonly<{ children: ReactNode }>) {
    return (
        <p className="mt-3 rounded-xl border border-dashed border-(--color-light) bg-(--colour-lightest) px-4 py-3 text-sm text-(--color-text)">
           <span className="font-semibold"> Known gap: </span>
            {children}
        </p>
    );
}

const SECTIONS = [
  { id: 'colour', label: 'Colour', icon: Palette },
  { id: 'typography', label: 'Typography', icon: Type },
  { id: 'logo', label: 'Logo & Icons', icon: Shapes },
  { id: 'tokens', label: 'Design Tokens', icon: Boxes },
  { id: 'components', label: 'Components', icon: LayoutGrid },
  { id: 'accessibility', label: 'Accessibility', icon: Accessibility },
  { id: 'voice', label: 'Voice & Tone', icon: MessageSquare },
  { id: 'changelog', label: 'Changelog', icon: History },
];

const COLOURS = [
  { name: 'Primary', token: '--color-primary', hex: '#231F20', text: 'text-white', usage: 'Sidebar background, headings & body text on white surfaces, modal/card text.' },
  { name: 'Secondary', token: '--color-secondary', hex: '#3DBF79', text: 'text-(--color-text)', usage: 'Active nav pill, primary/confirm buttons, input focus border.' },
  { name: 'Background', token: '--color-background', hex: '#FFFFFF', text: 'text-(--color-text)', usage: 'Card and form backgrounds, text on dark/green surfaces.', border: true },
  { name: 'Light', token: '--color-light', hex: '#A1A1A1', text: 'text-white', usage: 'Secondary/placeholder text, default input borders, card descriptions.' },
  { name: 'Lightest', token: '--color-lightest', hex: '#F2F2F2', text: 'text-(--color-text)', usage: 'Main content-area background behind the sidebar layout.', border: true },
  { name: 'Error', token: '--color-error', hex: '#e0a92e', text: 'text-white', usage: 'Reserved for error/destructive semantics (defined, not yet wired into any component).' },
];

const CONTRAST_ROWS = [
  { fg: '#231F20', bg: '#FFFFFF', ratio: '17.5:1', passes: 'All text, AAA' },
  { fg: '#FFFFFF', bg: '#231F20', ratio: '17.5:1', passes: 'All text, AAA' },
  { fg: '#231F20', bg: '#A1A1A1', ratio: '4.7:1', passes: 'Normal text, AA' },
  { fg: '#FFFFFF', bg: '#3DBF79', ratio: '2.8:1', passes: 'Large bold text only' },
  { fg: '#A1A1A1', bg: '#FFFFFF', ratio: '2.4:1', passes: 'Decorative / placeholder only' },
];

const TOKENS_CODE = `:root {
  --color-primary: #231F20;
  --color-secondary: #3DBF79;
  --color-background: #ffffff;
  --color-text: #231F20;
  --color-dark: #231F20;
  --color-light: #a1a1a1;
  --color-lightest: #F2F2F2;
  --color-error: #ef4444;
}

@theme inline {
  --font-sans: var(--font-afacad);
  --font-mono: var(--font-geist-mono);
}`;

const CHANGELOG = [
  { area: 'Colour palette', demo1: '4 colours (Black, White, Green, Grey #C3C3C3) + 4 semantic colours', demo2: 'Grey changed to #A1A1A1; #F2F2F2 added as content background; error red changed to #EF4444; no semantic status colours implemented yet' },
  { area: 'Typography — monospace', demo1: 'JetBrains Mono for machine-generated values', demo2: 'Geist Mono loaded instead; not yet applied to any specific content type' },
  { area: 'Typography — scale', demo1: 'Named modular scale (Display/H1–H4/Body/Caption)', demo2: 'No scale implemented; sizes set ad hoc per screen' },
  { area: 'Status badges', demo1: '4-state badge system with colour + aria-label per result', demo2: 'Not implemented; case status renders as a single green pill regardless of value' },
  { area: 'Buttons', demo1: '8 required states incl. danger, loading, focused, disabled', demo2: '2 states implemented per variant (default, hover); destructive delete action uses the green variant' },
  { area: 'Modal', demo1: 'Focus-trapped, 560px/80vh, black header, destructive dialogs immune to overlay-click', demo2: 'No focus trap, max-w-md, no header convention, overlay click always closes' },
  { area: 'Design principles', demo1: 'Glassmorphism explicitly deferred', demo2: 'Backdrop-blur and glow effects added to landing/login/register pages' },
  { area: 'Design tokens', demo1: 'Spacing/radius/shadow implied via 4px-multiple rule', demo2: 'No formal tokens; ad hoc utility values, repeated inline shadow pattern' },
  { area: 'Logo', demo1: 'Full lockup (circle + green divider + wordmark) with clear-space rule', demo2: 'Circle mark placed next to plain text, no divider, no enforced clear space' },
  { area: 'Sidebar', demo1: 'User avatar/name at footer', demo2: 'Footer contains only a Log Out button' },
  { area: 'Accessibility', demo1: 'Green focus ring, focus trap, aria-live, full ARIA coverage', demo2: 'Black focus ring on some components, no focus trap, no aria-live, partial ARIA coverage' },
];

export default function StyleGuidePage() {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-(--color-background) text-(--color-text)">
      {/* Hero */}
      <header className="relative overflow-hidden bg-(--color-primary) px-6 py-16 text-white sm:px-10 sm:py-24">
        <div className="relative z-10 mx-auto max-w-5xl">
          <div className="flex items-center gap-3">
            <Image src="/VL_Logo_light.svg" alt="Veritas Lab" width={48} height={48} className="size-10 sm:size-12" />
            <span className="text-xl font-semibold sm:text-2xl">Veritas Lab</span>
          </div>
          <h1 className="mt-8 max-w-3xl text-4xl font-bold sm:text-6xl">Brand &amp; Design System</h1>
          <p className="mt-4 max-w-2xl text-base text-(--color-light) sm:text-lg">
            The current, implemented design language behind Veritas Lab — colour, type, components and
            accessibility rules as they exist in the product today, not an aspirational spec.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3 text-sm text-(--color-light)">
            <span className="rounded-full bg-white/10 px-3 py-1">Team DeltaTech</span>
            <span className="rounded-full bg-white/10 px-3 py-1">Client: Naked Insurance</span>
            <span className="rounded-full bg-white/10 px-3 py-1">Demo 2 · 2026</span>
          </div>
        </div>
      </header>

      {/* Section nav */}
      <nav
        aria-label="Style guide sections"
        className="sticky top-0 z-40 flex gap-1 overflow-x-auto border-b border-(--color-lightest) bg-white/90 px-4 py-3 backdrop-blur sm:px-10"
      >
        {SECTIONS.map(({ id, label, icon: Icon }) => (
          <a
            key={id}
            href={`#${id}`}
            className="flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-sm font-medium text-(--color-text) transition-colors hover:bg-(--color-lightest)"
          >
            <Icon size={16} aria-hidden="true" />
            {label}
          </a>
        ))}
      </nav>

      <main className="mx-auto max-w-5xl px-6 py-16 sm:px-10">
        {/* 1. Colour */}
        <Reveal>
          <section id="colour" className="scroll-mt-24">
            <SectionHeading icon={Palette} title="1. Refined Colour Palette" />
            <p className="mt-3 max-w-3xl text-(--color-light)">
              Every colour used in the interface comes from the tokens below, defined in
              <code className="mx-1 rounded bg-(--color-lightest) px-1.5 py-0.5 font-mono text-sm">globals.css</code>.
            </p>

            <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3">
              {COLOURS.map((c) => (
                <div key={c.token} className={`overflow-hidden rounded-2xl ${c.border ? 'border border-(--color-lightest)' : ''}`}>
                  <div className={`flex h-20 items-end p-3 ${c.text}`} style={{ backgroundColor: c.hex }}>
                    <span className="text-xs font-semibold uppercase tracking-wide">{c.name}</span>
                  </div>
                  <div className="bg-(--color-lightest) p-3">
                    <p className="font-mono text-xs text-(--color-text)">{c.hex}</p>
                    <p className="mt-1 text-xs text-(--color-light)">{c.token}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 overflow-x-auto">
              <table className="w-full min-w-[420px] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-(--color-lightest) text-(--color-light)">
                    <th className="py-2 pr-4 font-semibold">Colour</th>
                    <th className="py-2 pr-4 font-semibold">Usage</th>
                  </tr>
                </thead>
                <tbody>
                  {COLOURS.map((c) => (
                    <tr key={c.token} className="border-b border-(--color-lightest)">
                      <td className="py-2 pr-4 font-medium">{c.name}</td>
                      <td className="py-2 pr-4 text-(--color-light)">{c.usage}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h3 className="mt-10 text-lg font-semibold">WCAG 2.2 contrast reference</h3>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[480px] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-(--color-lightest) text-(--color-light)">
                    <th className="py-2 pr-4 font-semibold">Foreground</th>
                    <th className="py-2 pr-4 font-semibold">Background</th>
                    <th className="py-2 pr-4 font-semibold">Ratio</th>
                    <th className="py-2 pr-4 font-semibold">Passes for</th>
                  </tr>
                </thead>
                <tbody>
                  {CONTRAST_ROWS.map((r) => (
                    <tr key={`${r.fg}-${r.bg}`} className="border-b border-(--color-lightest)">
                      <td className="flex items-center gap-2 py-2 pr-4 font-mono text-xs">
                        <span className="size-3 rounded-full border border-(--color-lightest)" style={{ backgroundColor: r.fg }} aria-hidden="true" />
                        {r.fg}
                      </td>
                      <td className="flex items-center gap-2 py-2 pr-4 font-mono text-xs">
                        <span className="size-3 rounded-full border border-(--color-lightest)" style={{ backgroundColor: r.bg }} aria-hidden="true" />
                        {r.bg}
                      </td>
                      <td className="py-2 pr-4 font-mono text-xs">{r.ratio}</td>
                      <td className="py-2 pr-4">{r.passes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <GapNote>
              No info-blue, or success-green tokens exist yet, so detection results (deepfake /
              authentic / inconclusive / processing) have no semantic colour mapping in the UI. The
              light-grey / white pairing also falls short of AA for normal text — it should stay limited to
              placeholders and large or decorative text until addressed.
            </GapNote>
          </section>
        </Reveal>