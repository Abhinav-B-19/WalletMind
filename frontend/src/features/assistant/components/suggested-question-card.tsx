import { Button } from "@/components/ui/button";

type SuggestedQuestionCardProps = {
  question: string;
  onClick: (question: string) => void;
};

export function SuggestedQuestionCard({
  question,
  onClick,
}: SuggestedQuestionCardProps) {
  return (
    <Button
      type="button"
      variant="secondary"
      className="h-auto justify-start whitespace-normal px-3 py-3 text-left"
      onClick={() => onClick(question)}
    >
      {question}
    </Button>
  );
}
