import Card from '@/components/ui/card';
export default function LandingHighlights() {
    return (
        <>
            <div className="flex flex-row gap-10 mt-5">
                <div className="flex flex-col gap-2">
                    <Card className="w-[400px] h-[300px] bg-(--color-light)">
                        <Card.Header>
                            <h3 className="font-bold text-lg">Feature Highlight 1</h3>
                        </Card.Header>
                        <Card.Content>
                            <p>Description of feature highlight 1.</p>
                        </Card.Content>
                    </Card>
                </div>
            </div>
        </>
    );
}