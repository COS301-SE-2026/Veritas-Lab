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
            <div className="flex flex-col w-full px-6 sm:px-10 py-10 sm:py-14">
                <p className="text-base sm:text-lg lg:text-xl text-(--color-light) tracking-wide">
                    WHO IT&apos;S FOR
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
                    {audiences.map((item) => {
                        const Icon = item.icon;
                        return (
                            <div key={item.title} className="rounded-2xl bg-(--color-lightest) p-5">
                                <div
                                    className="size-[60px] rounded-xl bg-(--color-background) flex items-center justify-center"
                                    aria-hidden="true"
                                >
                                    <Icon className="size-[40px] text-(--color-secondary)" />
                                </div>
                                <h3 className="text-(--color-text) text-lg sm:text-xl font-bold mt-6">
                                    {item.title}
                                </h3>
                                <p className="text-(--color-text) text-base sm:text-lg mt-3">
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