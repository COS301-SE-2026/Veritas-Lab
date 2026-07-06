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
        <div className="grid grid-cols-4 gap-1 mt-5 items-center align-center">
            {highlights.map((item) => {
                const Icon = item.icon;
                return (
                    <Card
                        key={item.title}
                        className="w-[80%] min-h-[300px] rounded-2xl bg-(--color-lightest) p-5"
                    >
                        <Card.Header>
                            <div
                                className="size-[60px] rounded-xl bg-(--color-background) flex items-center justify-center"
                                aria-hidden="true"
                            >
                                <Icon className="size-[40px] text-(--color-secondary)" />
                            </div>
                        </Card.Header>
                        <Card.Content className="mt-10">
                            <h3 className="text-(--color-text) text-xl font-bold">{item.title}</h3>
                            <p className="text-(--color-text) text-lg mt-5">{item.description}</p>
                        </Card.Content>
                    </Card>
                );
            })}
        </div>
    );
}