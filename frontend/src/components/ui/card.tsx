import type { CardProps } from '@/types/components';
import type { CardSectionProps } from '@/types/components';


function CardHeader({ children, className }: CardSectionProps) {
    return <div className={className || 'card-header'}>{children}</div>;
}

function CardContent({ children, className }: CardSectionProps) {
    return <div className={className || 'card-content'}>{children}</div>;
}

function CardFooter({ children, className }: CardSectionProps) {
    return <div className={`mt-auto ${className || 'card-footer'}`}>{children}</div>;
}

function Card({ children, header, content, footer, className, headerClassName, contentClassName, footerClassName }: CardProps) {
    const hasCompoundChildren = Boolean(children);

    return (
        <div className={`flex flex-col ${className || ''}`}>
            {hasCompoundChildren ? (
                children
            ) : (
                <>
                    {header ? <div className={headerClassName || 'card-header'}>{header}</div> : null}
                    {content ? <div className={contentClassName || 'card-content'}>{content}</div> : null}
                    {footer ? <div className={`mt-auto ${footerClassName || 'card-footer'}`}>{footer}</div> : null}
                </>
            )}
        </div>
    );
}

Card.Header = CardHeader;
Card.Content = CardContent;
Card.Footer = CardFooter;

export default Card;