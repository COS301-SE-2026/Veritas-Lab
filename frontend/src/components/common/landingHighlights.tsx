import Card from '@/components/ui/card';
import { ScanSearch, ClipboardCheck, ShieldAlert, Bot } from 'lucide-react';
import type { Highlight } from '@/types/components';

const highlights: Highlight[] = [
    { title: 'AI-powered analysis', description: 'Analyze media content with AI-powered insights.', icon: ScanSearch },
    { title: 'Content review', description: 'Assess and review media content with powerful tools.', icon: ClipboardCheck },
    { title: 'Tamper detection', description: 'Identify tampered and manipulated media content.', icon: ShieldAlert },
    { title: 'Deepfake detection', description: 'Detect deepfakes and other AI-generated content.', icon: Bot },
];

export default function LandingHighlights() {
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mt-6">
            {highlights.map((item) => {
                const Icon = item.icon;
                return (
                    <Card
                        key={item.title}
                        className="vl-card vl-card-interactive w-full min-h-[220px] sm:min-h-[260px] p-6"
                    >
                        <Card.Header>
                            <div
                                className="flex size-14 items-center justify-center rounded-2xl bg-(--color-b-50) ring-1 ring-[color-mix(in_srgb,var(--b-500)_25%,transparent)]"
                                aria-hidden="true"
                            >
                                <Icon className="size-7 text-(--color-b-600)" />
                            </div>
                        </Card.Header>
                        <Card.Content className="mt-6 sm:mt-8">
                            <h3 className="text-(--color-text-strong) text-lg sm:text-xl font-bold">{item.title}</h3>
                            <p className="text-(--color-text-muted) text-base mt-2.5 leading-relaxed">{item.description}</p>
                        </Card.Content>
                    </Card>
                );
            })}
        </div>
    );
}