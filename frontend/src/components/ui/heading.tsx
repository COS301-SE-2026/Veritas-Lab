import React from "react";
//Basic heading component for now, more styles and props may be added later
type HeadingProps = {
    text: string;
};
export default function Heading({ text }: HeadingProps) {
    return (
        <h1>{text}</h1>
    );
}