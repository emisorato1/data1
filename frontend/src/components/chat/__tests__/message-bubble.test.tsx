import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MessageBubble } from "../message-bubble";
import type { Message } from "../message-bubble";

// Mock next/image
vi.mock("next/image", () => ({
  default: (props: Record<string, unknown>) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />;
  },
}));

const assistantMessage: Message = {
  id: "msg-1",
  role: "assistant",
  content: "Esta es una respuesta del asistente.",
  sources: [
    { index: 1, document_name: "Doc A", page: 3, chunk_text: "Chunk A" },
  ],
};

const userMessage: Message = {
  id: "msg-2",
  role: "user",
  content: "Hola, tengo una consulta.",
};

const streamingMessage: Message = {
  id: "msg-3",
  role: "assistant",
  content: "",
  isStreaming: true,
};

describe("MessageBubble", () => {
  it("renders feedback buttons for assistant messages (always visible)", () => {
    render(<MessageBubble message={assistantMessage} />);

    const feedbackUp = screen.getByLabelText("Respuesta útil");
    const feedbackDown = screen.getByLabelText("Respuesta no útil");

    expect(feedbackUp).toBeInTheDocument();
    expect(feedbackDown).toBeInTheDocument();

    // The feedback widget container should NOT have opacity-0
    const actionContainer = feedbackUp.closest("[class*='flex items-center gap-1']");
    if (actionContainer) {
      expect(actionContainer.className).not.toContain("opacity-0");
    }
  });

  it("feedback buttons meet 44x44px minimum size", () => {
    render(<MessageBubble message={assistantMessage} />);

    const feedbackUp = screen.getByLabelText("Respuesta útil");
    expect(feedbackUp.className).toContain("min-w-[44px]");
    expect(feedbackUp.className).toContain("min-h-[44px]");
  });

  it("does not render feedback buttons for user messages", () => {
    render(<MessageBubble message={userMessage} />);
    expect(screen.queryByLabelText("Respuesta útil")).not.toBeInTheDocument();
  });

  it("does not render feedback buttons while streaming", () => {
    render(<MessageBubble message={streamingMessage} />);
    expect(screen.queryByLabelText("Respuesta útil")).not.toBeInTheDocument();
  });

  it("copy button has hover-only visibility", () => {
    render(<MessageBubble message={assistantMessage} />);
    const copyBtn = screen.getByLabelText("Copiar respuesta");
    expect(copyBtn.className).toContain("opacity-0");
    expect(copyBtn.className).toContain("group-hover:opacity-100");
  });

  it("renders message content for assistant", () => {
    render(<MessageBubble message={assistantMessage} />);
    expect(screen.getByText("Esta es una respuesta del asistente.")).toBeInTheDocument();
  });

  it("renders message content for user", () => {
    render(<MessageBubble message={userMessage} />);
    expect(screen.getByText("Hola, tengo una consulta.")).toBeInTheDocument();
  });

  it("shows streaming indicator when streaming with no content", () => {
    render(<MessageBubble message={streamingMessage} />);
    expect(screen.getByText("Analizando documentos...")).toBeInTheDocument();
  });

  it("shows sources section for assistant messages with sources", () => {
    render(<MessageBubble message={assistantMessage} />);
    expect(screen.getByText("Fuentes")).toBeInTheDocument();
    expect(screen.getByText("Doc A")).toBeInTheDocument();
  });
});
