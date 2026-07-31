import type { HeadingProps } from "@/types/components";
//Basic heading component for now, more styles and props may be added later
export default function Heading({ text }: HeadingProps) {
    return (
        <h1>{text}</h1>
    );
}