import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";

interface FeedbackWidgetProps {
  messageId: string;
}

export function FeedbackWidget({ messageId }: FeedbackWidgetProps) {
  const [rating, setRating] = useState<"positive" | "negative" | null>(null);
  const [comment, setComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleFeedback = async (newRating: "positive" | "negative", currentComment: string = "") => {
    setIsSubmitting(true);
    setRating(newRating);

    try {
      const res = await fetch("/api/v1/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message_id: messageId,
          rating: newRating,
          comment: currentComment,
        }),
      });

      if (!res.ok) {
        throw new Error("Error submitting feedback");
      }

      setIsSuccess(true);

      setTimeout(() => {
        setIsSuccess(false);
      }, 3000);

    } catch (error) {
      console.error(error);
      setRating(null);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCommentSubmit = () => {
    if (rating === "negative") {
      handleFeedback("negative", comment);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-1.5">
        <button
          className={`min-w-[44px] min-h-[44px] inline-flex items-center justify-center rounded-lg transition-all ${
            rating === "positive"
              ? "text-green-600 bg-green-50 dark:bg-green-950/30"
              : "text-muted-foreground hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-950/30"
          }`}
          onClick={() => handleFeedback("positive")}
          disabled={isSubmitting || rating !== null}
          title="Útil"
          aria-label="Respuesta útil"
        >
          <ThumbsUp className="w-5 h-5" />
        </button>
        <button
          className={`min-w-[44px] min-h-[44px] inline-flex items-center justify-center rounded-lg transition-all ${
            rating === "negative"
              ? "text-red-600 bg-red-50 dark:bg-red-950/30"
              : "text-muted-foreground hover:text-destructive hover:bg-red-50 dark:hover:bg-red-950/30"
          }`}
          onClick={() => setRating("negative")}
          disabled={isSubmitting || rating === "positive"}
          title="No útil"
          aria-label="Respuesta no útil"
        >
          <ThumbsDown className="w-5 h-5" />
        </button>

        {isSuccess && (
          <span className="text-xs text-green-600 ml-2 animate-in fade-in">
            ¡Gracias por tu feedback!
          </span>
        )}
      </div>

      {rating === "negative" && !isSuccess && (
        <div className="flex flex-col gap-2 w-full min-w-[250px] animate-in slide-in-from-top-2">
          <textarea
            placeholder="¿En qué podemos mejorar esta respuesta? (opcional)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
            disabled={isSubmitting}
          />
          <div className="flex justify-end gap-2">
            <button
              className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-4"
              onClick={() => {
                setRating(null);
                setComment("");
              }}
              disabled={isSubmitting}
            >
              Cancelar
            </button>
            <button
              className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-4"
              onClick={handleCommentSubmit}
              disabled={isSubmitting}
            >
              Enviar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
