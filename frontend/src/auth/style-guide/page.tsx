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

