import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationPanel } from "@/components/TranslationPanel";

describe("TranslationPanel", () => {
  it("shows placeholder when no pages", () => {
    render(<TranslationPanel pages={[]} currentPage={1} />);
    expect(screen.getByTestId("translation-panel")).toBeDefined();
    expect(screen.getByText(/Turkce ceviri/i)).toBeDefined();
  });

  it("shows processing message during translation", () => {
    render(<TranslationPanel pages={[]} currentPage={1} status="processing" />);
    expect(screen.getByText(/baslatildi/i)).toBeDefined();
  });

  it("shows translated pages as they arrive", () => {
    render(
      <TranslationPanel
        pages={[{ page: 1, content: "Translated page 1 content" }]}
        currentPage={1}
      />
    );
    expect(screen.getByText("Translated page 1 content")).toBeDefined();
  });

  it("shows page number", () => {
    render(
      <TranslationPanel
        pages={[{ page: 3, content: "Page 3 translation" }]}
        currentPage={3}
      />
    );
    expect(screen.getByText("Sayfa 3")).toBeDefined();
  });
});
