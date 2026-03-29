import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { FeedbackWidget } from "./FeedbackWidget";
import { describe, it, expect, vi, beforeEach } from "vitest";

global.fetch = vi.fn();

describe("FeedbackWidget", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders thumbs up and down buttons", () => {
    render(<FeedbackWidget messageId="123" />);
    expect(screen.getByLabelText("Respuesta útil")).toBeInTheDocument();
    expect(screen.getByLabelText("Respuesta no útil")).toBeInTheDocument();
  });

  it("buttons meet 44x44px minimum touch target", () => {
    render(<FeedbackWidget messageId="123" />);
    const thumbsUp = screen.getByLabelText("Respuesta útil");
    const thumbsDown = screen.getByLabelText("Respuesta no útil");

    // Check min-width/min-height classes are present
    expect(thumbsUp.className).toContain("min-w-[44px]");
    expect(thumbsUp.className).toContain("min-h-[44px]");
    expect(thumbsDown.className).toContain("min-w-[44px]");
    expect(thumbsDown.className).toContain("min-h-[44px]");
  });

  it("buttons do not require hover to be visible (no opacity-0 class)", () => {
    render(<FeedbackWidget messageId="123" />);
    const thumbsUp = screen.getByLabelText("Respuesta útil");
    const container = thumbsUp.closest("div");
    expect(container?.className).not.toContain("opacity-0");
  });

  it("handles positive feedback click", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ ok: true });

    render(<FeedbackWidget messageId="123" />);

    const thumbsUp = screen.getByLabelText("Respuesta útil");
    fireEvent.click(thumbsUp);

    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/feedback",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          message_id: "123",
          rating: "positive",
          comment: "",
        }),
      })
    );

    await waitFor(() => {
      expect(screen.getByText("¡Gracias por tu feedback!")).toBeInTheDocument();
    });
  });

  it("shows text area when negative feedback is clicked", () => {
    render(<FeedbackWidget messageId="123" />);

    const thumbsDown = screen.getByLabelText("Respuesta no útil");
    fireEvent.click(thumbsDown);

    expect(screen.getByPlaceholderText(/en qué podemos mejorar/i)).toBeInTheDocument();
    expect(screen.getByText("Enviar")).toBeInTheDocument();
    expect(screen.getByText("Cancelar")).toBeInTheDocument();
  });

  it("handles negative feedback with comment", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ ok: true });

    render(<FeedbackWidget messageId="123" />);

    const thumbsDown = screen.getByLabelText("Respuesta no útil");
    fireEvent.click(thumbsDown);

    const textarea = screen.getByPlaceholderText(/en qué podemos mejorar/i);
    fireEvent.change(textarea, { target: { value: "Respuesta incorrecta" } });

    const sendBtn = screen.getByText("Enviar");
    fireEvent.click(sendBtn);

    expect(global.fetch).toHaveBeenCalledWith(
      "/api/v1/feedback",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          message_id: "123",
          rating: "negative",
          comment: "Respuesta incorrecta",
        }),
      })
    );
  });

  it("cancel button resets negative feedback state", () => {
    render(<FeedbackWidget messageId="123" />);

    fireEvent.click(screen.getByLabelText("Respuesta no útil"));
    expect(screen.getByPlaceholderText(/en qué podemos mejorar/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText("Cancelar"));
    expect(screen.queryByPlaceholderText(/en qué podemos mejorar/i)).not.toBeInTheDocument();
  });

  it("disables both buttons after positive feedback", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ ok: true });

    render(<FeedbackWidget messageId="123" />);

    fireEvent.click(screen.getByLabelText("Respuesta útil"));

    await waitFor(() => {
      expect(screen.getByLabelText("Respuesta útil")).toBeDisabled();
      expect(screen.getByLabelText("Respuesta no útil")).toBeDisabled();
    });
  });

  it("resets rating on API error", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error("Network error"));

    render(<FeedbackWidget messageId="123" />);

    fireEvent.click(screen.getByLabelText("Respuesta útil"));

    await waitFor(() => {
      expect(screen.getByLabelText("Respuesta útil")).not.toBeDisabled();
    });
  });
});
