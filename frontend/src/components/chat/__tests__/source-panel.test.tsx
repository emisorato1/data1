import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { SourcePanel } from "../source-panel";
import type { Source } from "../message-bubble";

const mockSource: Source = {
  index: 1,
  document_name: "Manual de Operaciones",
  page: 5,
  chunk_text: "Este es un extracto del documento.",
};

const mockSources: Source[] = [
  mockSource,
  { index: 2, document_name: "Política RRHH", page: 12, chunk_text: "Otro extracto." },
];

describe("SourcePanel", () => {
  it("renders nothing when source is null", () => {
    const { container } = render(
      <SourcePanel
        source={null}
        sources={[]}
        onClose={vi.fn()}
        onSelectSource={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders with dynamic width when width prop is provided", () => {
    render(
      <SourcePanel
        source={mockSource}
        sources={mockSources}
        onClose={vi.fn()}
        onSelectSource={vi.fn()}
        width={450}
      />
    );

    const aside = screen.getByRole("complementary");
    expect(aside.style.width).toBe("450px");
    expect(aside.style.minWidth).toBe("450px");
  });

  it("renders with default 320px when no width prop", () => {
    render(
      <SourcePanel
        source={mockSource}
        sources={mockSources}
        onClose={vi.fn()}
        onSelectSource={vi.fn()}
      />
    );

    const aside = screen.getByRole("complementary");
    expect(aside.style.width).toBe("320px");
  });

  it("renders resize gutter when onGutterMouseDown is provided", () => {
    render(
      <SourcePanel
        source={mockSource}
        sources={mockSources}
        onClose={vi.fn()}
        onSelectSource={vi.fn()}
        onGutterMouseDown={vi.fn()}
        width={400}
      />
    );

    const gutter = screen.getByRole("separator");
    expect(gutter).toBeInTheDocument();
    expect(gutter).toHaveAttribute("aria-label", "Redimensionar panel de fuentes");
    expect(gutter).toHaveAttribute("aria-orientation", "vertical");
  });

  it("does not render gutter when onGutterMouseDown is not provided", () => {
    render(
      <SourcePanel
        source={mockSource}
        sources={mockSources}
        onClose={vi.fn()}
        onSelectSource={vi.fn()}
      />
    );

    expect(screen.queryByRole("separator")).not.toBeInTheDocument();
  });

  it("calls onGutterMouseDown when gutter is pressed", () => {
    const onGutter = vi.fn();
    render(
      <SourcePanel
        source={mockSource}
        sources={mockSources}
        onClose={vi.fn()}
        onSelectSource={vi.fn()}
        onGutterMouseDown={onGutter}
        width={400}
      />
    );

    fireEvent.mouseDown(screen.getByRole("separator"));
    expect(onGutter).toHaveBeenCalledTimes(1);
  });

  it("applies dragging style when isDragging is true", () => {
    render(
      <SourcePanel
        source={mockSource}
        sources={mockSources}
        onClose={vi.fn()}
        onSelectSource={vi.fn()}
        onGutterMouseDown={vi.fn()}
        width={400}
        isDragging={true}
      />
    );

    const gutter = screen.getByRole("separator");
    expect(gutter.className).toContain("bg-primary/30");
  });

  it("displays source document name and page", () => {
    render(
      <SourcePanel
        source={mockSource}
        sources={mockSources}
        onClose={vi.fn()}
        onSelectSource={vi.fn()}
      />
    );

    expect(screen.getByText("Manual de Operaciones")).toBeInTheDocument();
    expect(screen.getByText("Página 5")).toBeInTheDocument();
  });

  it("displays chunk text excerpt", () => {
    render(
      <SourcePanel
        source={mockSource}
        sources={mockSources}
        onClose={vi.fn()}
        onSelectSource={vi.fn()}
      />
    );

    expect(screen.getByText("Este es un extracto del documento.")).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(
      <SourcePanel
        source={mockSource}
        sources={mockSources}
        onClose={onClose}
        onSelectSource={vi.fn()}
      />
    );

    fireEvent.click(screen.getByLabelText("Cerrar panel de fuentes"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("renders source navigation chips when multiple sources exist", () => {
    render(
      <SourcePanel
        source={mockSource}
        sources={mockSources}
        onClose={vi.fn()}
        onSelectSource={vi.fn()}
      />
    );

    expect(screen.getByText("Todas las fuentes")).toBeInTheDocument();
    expect(screen.getByLabelText("Fuente 1: Manual de Operaciones")).toBeInTheDocument();
    expect(screen.getByLabelText("Fuente 2: Política RRHH")).toBeInTheDocument();
  });

  it("calls onSelectSource when a navigation chip is clicked", () => {
    const onSelect = vi.fn();
    render(
      <SourcePanel
        source={mockSource}
        sources={mockSources}
        onClose={vi.fn()}
        onSelectSource={onSelect}
      />
    );

    fireEvent.click(screen.getByLabelText("Fuente 2: Política RRHH"));
    expect(onSelect).toHaveBeenCalledWith(2);
  });
});
