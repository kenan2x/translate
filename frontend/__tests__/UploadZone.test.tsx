import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { UploadZone } from "@/components/UploadZone";

describe("UploadZone", () => {
  it("renders upload area", () => {
    render(<UploadZone onUpload={vi.fn()} />);
    expect(screen.getByTestId("upload-zone")).toBeDefined();
    expect(screen.getByText(/PDF/i)).toBeDefined();
  });

  it("calls onUpload when valid PDF selected", () => {
    const onUpload = vi.fn();
    render(<UploadZone onUpload={onUpload} />);
    const input = screen.getByTestId("file-input") as HTMLInputElement;
    const file = new File(["%PDF-test"], "test.pdf", { type: "application/pdf" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(onUpload).toHaveBeenCalledWith(file);
  });

  it("rejects non-PDF files", () => {
    const onUpload = vi.fn();
    render(<UploadZone onUpload={onUpload} />);
    const input = screen.getByTestId("file-input") as HTMLInputElement;
    const file = new File(["text"], "test.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(onUpload).not.toHaveBeenCalled();
    expect(screen.getByTestId("upload-error")).toBeDefined();
  });

  it("disables when disabled prop is true", () => {
    render(<UploadZone onUpload={vi.fn()} disabled />);
    const input = screen.getByTestId("file-input") as HTMLInputElement;
    expect(input.disabled).toBe(true);
  });
});
