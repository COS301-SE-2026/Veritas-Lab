type CardProps = {
    header: string | React.ReactNode;
    content: string | React.ReactNode;
    footer: string | React.ReactNode;
};

export default function Card({ header, content, footer }: CardProps) {
    return (
        <div>
            <div className="card-header">{header}</div>
            <div className="card-content">{content}</div>
            <div className="card-footer">{footer}</div>
         </div>
    );
}