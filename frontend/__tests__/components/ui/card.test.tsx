import { render, screen } from "@testing-library/react";
import Card from "@/components/ui/card";

describe("Card component", () => {
    it("renders header, content, and footer correctly", () => {
        render(<Card
            header="Test Header"
            content="This is the content of the card."
            footer="Test Footer"
        />);    
        expect(screen.getByText("Test Header")).toBeInTheDocument();
        expect(screen.getByText("This is the content of the card.")).toBeInTheDocument();
        expect(screen.getByText("Test Footer")).toBeInTheDocument();
    });
});