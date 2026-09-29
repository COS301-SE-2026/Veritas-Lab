import { ShieldQuestion, Newspaper, Scale, Landmark } from 'lucide-react';
import type { Audience } from '@/types/components';

const audiences: Audience[] = [
    { title: 'Claims investigators', description: 'Test the photos and documents attached to a claim before a payout is approved.', icon: ShieldQuestion },
    { title: 'Journalists & fact-checkers', description: 'Verify user-submitted footage under deadline, with a record of what you checked.', icon: Newspaper },
    { title: 'Legal & compliance teams', description: 'Build an evidence trail that holds up when a finding is contested.', icon: Scale },
    { title: 'Forensic analysts', description: 'Triage large media sets fast, then dig into the frames the engines flag.', icon: Landmark },
];

export default function LandingAudience() {
    return (
        <section className="bg-white">
            <div className="flex flex-col w-full px-6 sm:px-10 py-12 sm:py-16">
                <p className="text-xs sm:text-sm font-semibold uppercase tracking-[0.2em] text-(--color-text-subtle)">
                    Who it&apos;s for
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mt-6">
                    {audiences.map((item) => {
                        const Icon = item.icon;
                        return (
                            <div key={item.title} className="vl-card vl-card-interactive p-6">
                                <div
                                    className="flex size-14 items-center justify-center rounded-2xl bg-(--color-b-50) ring-1 ring-[color-mix(in_srgb,var(--b-500)_25%,transparent)]"
                                    aria-hidden="true"
                                >
                                    <Icon className="size-7 text-(--color-b-600)" />
                                </div>
                                <h3 className="text-(--color-text-strong) text-lg sm:text-xl font-bold mt-6">
                                    {item.title}
                                </h3>
                                <p className="text-(--color-text-muted) text-base mt-2.5 leading-relaxed">
                                    {item.description}
                                </p>
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}