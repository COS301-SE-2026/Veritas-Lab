import Card from "../ui/card";

type EvidenceCardProps = {
    fileName: string;
    preview?: string;
    properties: string;
};
export default function EvidenceCard({ fileName, preview, properties }: EvidenceCardProps) {
    return (
        <Card
            header={fileName}
            headerClassName="   text-[18px] font-semibold mb-2"
            content={preview}
            contentClassName="text-[16px] text-gray-600"
            footer={properties}
            footerClassName="text-sm text-gray-500 mt-2 align-bottom"
            className="shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] rounded-[21px] p-4 w-[228px] h-[200px] text-[var(--color-text)]"
        />
    );
}