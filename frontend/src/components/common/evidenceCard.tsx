import Link from "next/link";
import Card from "../ui/card";
import type { EvidenceCardProps } from "@/types/components";
export default function EvidenceCard({ mediaName, mediaUrl, mediaExtension, href }: Readonly<EvidenceCardProps>) {
    const card = (
        <Card
            header={mediaName}
            headerClassName="   text-[18px] font-semibold mb-2"
            content={(
                <>
                    <div className="flex h-24 items-center justify-center overflow-hidden rounded-[14px] bg-black/5">
                        <img
                            src={mediaUrl}
                            alt={mediaName}
                            className="max-h-16 max-w-16 object-contain"
                        />
                        {/* this wil be for the image when we make image there. */}

                    </div>
                    {/* <div className="flex h-24 items-center justify-center overflow-hidden rounded-[14px] bg-black/5">
                        <div className="text-center">

                        </div>
                    </div> */}
                </>
            )}
            contentClassName="text-[16px] text-(--color-light)"
            footer={mediaExtension}
            footerClassName="text-sm text-(--color-light)"
            className="shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] rounded-[21px] p-4 w-[228px] h-[200px] text-[var(--color-text)]"
        />
    );

    if (href) {
        return (
            <Link
                href={href}
                className="block rounded-[21px] transition hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:ring-offset-2"
            >
                {card}
            </Link>
        );
    }

    return card;
}