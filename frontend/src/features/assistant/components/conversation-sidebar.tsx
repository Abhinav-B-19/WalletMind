import { SectionCard } from "@/features/ai-dashboard/components/section-card";

type ConversationSidebarProps = {
  messageCount: number;
};

export function ConversationSidebar({
  messageCount,
}: ConversationSidebarProps) {
  return (
    <SectionCard
      title="Conversation Sidebar"
      description="Future-ready area for conversation history, pinned threads, and saved prompts."
    >
      <p className="text-sm text-[var(--text-muted)]">
        Current messages in this session: {messageCount}
      </p>
    </SectionCard>
  );
}
