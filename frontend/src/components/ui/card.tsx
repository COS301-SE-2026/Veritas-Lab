type CardProps = {
    header: string | React.ReactNode;
    content: string | React.ReactNode;
    footer: string | React.ReactNode;
    className?: string;
    headerClassName?: string;
    contentClassName?: string;
    footerClassName?: string;
};

export default function Card({ header, content, footer, className, headerClassName, contentClassName, footerClassName }: CardProps) {
    return (
        <div className={`flex flex-col ${className}`}>
            <div className={headerClassName || "card-header"}>{header}</div>
            <div className={contentClassName || "card-content"}>{content}</div>
            <div className={`mt-auto ${footerClassName || "card-footer"}`}>{footer}</div>
        </div>
    );
}