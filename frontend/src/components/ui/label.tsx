//Label component for now more props may be added later
type labelProps = {
    text: string;
    htmlFor: string;
};

export default function Label({ text, htmlFor }: labelProps) {
    return (
        <label htmlFor={htmlFor}>{text}</label>
    );
}