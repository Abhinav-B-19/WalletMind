import { useCallback, useState, type KeyboardEvent } from "react";
import {
  ArrowRight,
  BookOpen,
  Bot,
  Boxes,
  CheckCircle2,
  ClipboardList,
  CloudCog,
  FileCode2,
  FileText,
  FolderGit2,
  GraduationCap,
  Layers,
  Milestone,
  type LucideIcon,
  Network,
  PlayCircle,
  Rocket,
  Scale,
  Workflow,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { PageTitle, SectionTitle } from "@/components/ui/section-title";

type JudgeCard = {
  title: string;
  description: string;
  actionLabel: string;
  href: string;
  icon: LucideIcon;
  comingSoon?: boolean;
};

const PROJECT_ROOT = "https://github.com/Abhinav-B-19/WalletMind";
const DOC_ROOT = `${PROJECT_ROOT}/blob/main/docs/judge`;

const QUICK_ACTIONS: JudgeCard[] = [
  {
    title: "Agent Playground",
    description:
      "Run coordinator and specialized agents, then inspect execution timeline and per-agent outputs.",
    actionLabel: "Open Demo",
    href: "/app/agent-playground",
    icon: Workflow,
  },
  {
    title: "REST Swagger",
    description:
      "Inspect live REST endpoints used by dashboard, statements, assistant, and orchestration flows.",
    actionLabel: "Open Swagger",
    href: "http://localhost:8000/docs",
    icon: FileCode2,
  },
  {
    title: "MCP Swagger",
    description:
      "Inspect MCP infrastructure and execution endpoints exposing WalletMind capabilities.",
    actionLabel: "Open Swagger",
    href: "http://localhost:8100/docs",
    icon: Network,
  },
];

const DOCUMENTATION_CARDS: JudgeCard[] = [
  {
    title: "Architecture",
    description:
      "View system architecture, ADK workflow, coordinator design, MCP integration, and Mermaid diagrams.",
    actionLabel: "Open Documentation",
    href: `${DOC_ROOT}/ARCHITECTURE.md`,
    icon: Layers,
  },
  {
    title: "Quick Start",
    description:
      "Launch backend, frontend, and MCP server quickly with a judge-optimized execution path.",
    actionLabel: "Open Documentation",
    href: `${DOC_ROOT}/QUICK_START.md`,
    icon: Rocket,
  },
  {
    title: "Demo Guide",
    description:
      "Follow step-by-step scenarios from upload to timeline, cards, and coordinator evidence.",
    actionLabel: "Open Documentation",
    href: `${DOC_ROOT}/DEMO_GUIDE.md`,
    icon: Milestone,
  },
  {
    title: "Rubric Mapping",
    description:
      "Map evaluation rubric items to concrete implementation files and runtime evidence.",
    actionLabel: "Open Documentation",
    href: `${DOC_ROOT}/RUBRIC_MAPPING.md`,
    icon: ClipboardList,
  },
  {
    title: "Project Overview",
    description:
      "Review repository overview, stack, setup flow, and project-level positioning.",
    actionLabel: "Open Documentation",
    href: `${PROJECT_ROOT}/blob/main/README.md`,
    icon: BookOpen,
  },
];

const SUBMISSION_ASSETS: JudgeCard[] = [
  {
    title: "GitHub Repository",
    description:
      "Browse source, tests, documentation, and sprint delivery artifacts in one place.",
    actionLabel: "Open GitHub",
    href: PROJECT_ROOT,
    icon: FolderGit2,
  },
  {
    title: "Kaggle Notebook",
    description:
      "Notebook showcase is not published yet. This card points to the planned submission slot.",
    actionLabel: "Coming Soon",
    href: "kaggle-coming-soon",
    icon: GraduationCap,
    comingSoon: true,
  },
  {
    title: "Demo Video",
    description:
      "Recorded walkthrough is not published yet. This card points to the planned demo section.",
    actionLabel: "Coming Soon",
    href: "demo-video-coming-soon",
    icon: PlayCircle,
    comingSoon: true,
  },
];

const STATUS_BADGES = [
  "Google ADK",
  "Multi-Agent",
  "Coordinator",
  "MCP Server",
  "Agent Playground",
  "Production APIs",
];

const EVALUATION_FLOW = [
  "Start Demo",
  "Upload Statement",
  "Dashboard",
  "Agent Playground",
  "Coordinator",
  "Execution Timeline",
  "Per-Agent Results",
];

type JudgeCardSectionProps = {
  title: string;
  subtitle: string;
  cards: JudgeCard[];
  onCardAction: (card: JudgeCard) => void;
};

function JudgeCardSection({
  title,
  subtitle,
  cards,
  onCardAction,
}: JudgeCardSectionProps) {
  const handleCardKeyDown = (
    event: KeyboardEvent<HTMLDivElement>,
    card: JudgeCard,
  ) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onCardAction(card);
    }
  };

  return (
    <section className="space-y-3">
      <SectionTitle title={title} subtitle={subtitle} />
      <div className="grid items-stretch gap-4 md:grid-cols-2 lg:grid-cols-3">
        {cards.map((card) => {
          const Icon = card.icon;

          return (
            <div
              key={card.title}
              role="button"
              tabIndex={0}
              aria-label={`${card.title} card`}
              data-testid="judge-hub-card-wrapper"
              className="h-full rounded-[var(--radius-lg)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
              onClick={() => onCardAction(card)}
              onKeyDown={(event) => handleCardKeyDown(event, card)}
            >
              <Card
                className="group h-full cursor-pointer overflow-hidden border-[var(--border)] transition-[background-color,border-color,box-shadow,transform] duration-[var(--duration-normal)] hover:-translate-y-0.5 hover:border-[var(--primary)]/50 hover:bg-[var(--surface-soft)] hover:shadow-[var(--shadow-md)]"
                data-testid="judge-hub-card"
              >
                <CardHeader className="pb-3">
                  <div className="mb-3 inline-flex w-fit items-center rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-2.5 transition-colors duration-[var(--duration-normal)] group-hover:bg-[var(--surface)]">
                    <Icon className="h-[var(--icon-md)] w-[var(--icon-md)] text-[var(--primary)] transition-transform duration-[var(--duration-normal)] group-hover:translate-x-0.5" />
                  </div>
                  <CardTitle className="text-lg">{card.title}</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col gap-3">
                  <p className="text-sm text-[var(--text-muted)]">
                    {card.description}
                  </p>
                  <div
                    className="mt-auto border-t border-[var(--border)] pt-3"
                    data-testid="judge-card-footer"
                  >
                    <button
                      type="button"
                      aria-label={`${card.title} action`}
                      className="inline-flex w-full items-center justify-between gap-2 rounded-[var(--radius-md)] bg-transparent px-1.5 py-1.5 text-sm font-medium text-[var(--text)] transition-colors duration-[var(--duration-normal)] hover:bg-[var(--surface-soft)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
                      onClick={(event) => {
                        event.stopPropagation();
                        onCardAction(card);
                      }}
                    >
                      <span>{card.actionLabel}</span>
                      {card.comingSoon ? null : (
                        <ArrowRight className="h-[var(--icon-sm)] w-[var(--icon-sm)] transition-transform duration-[var(--duration-normal)] group-hover:translate-x-0.5" />
                      )}
                    </button>
                  </div>
                </CardContent>
              </Card>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export function JudgeHubPage() {
  const [isComingSoonOpen, setIsComingSoonOpen] = useState(false);

  const openInNewTab = useCallback((href: string) => {
    window.open(href, "_blank", "noopener,noreferrer");
  }, []);

  const handleCardAction = useCallback(
    (card: JudgeCard) => {
      if (card.comingSoon) {
        setIsComingSoonOpen(true);
        return;
      }

      openInNewTab(card.href);
    },
    [openInNewTab],
  );

  return (
    <div className="space-y-6" aria-label="Judge hub page" id="judge-root">
      <section className="space-y-4" data-testid="judge-hero-section">
        <PageTitle
          title="WalletMind Judge Hub"
          subtitle="Google ADK + MCP Multi-Agent Financial Intelligence Platform"
        />

        <Card>
          <CardContent className="space-y-4 p-5">
            <div className="flex flex-wrap gap-2">
              {STATUS_BADGES.map((item) => (
                <span
                  key={item}
                  className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-1 text-xs font-medium text-[var(--text)]"
                >
                  <CheckCircle2 className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[#29d0b3]" />
                  {item}
                </span>
              ))}
            </div>

            <div
              className="flex flex-wrap gap-3"
              data-testid="judge-hero-actions"
            >
              <Button
                type="button"
                aria-label="Start demo"
                onClick={() => openInNewTab("/app/agent-playground")}
              >
                ▶ Start Demo
              </Button>
              <Button
                type="button"
                variant="secondary"
                aria-label="View architecture"
                onClick={() => openInNewTab(`${DOC_ROOT}/ARCHITECTURE.md`)}
              >
                📄 View Architecture
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>

      <JudgeCardSection
        title="Quick Actions"
        subtitle="Operational entry points for live evaluation during judge demos."
        cards={QUICK_ACTIONS}
        onCardAction={handleCardAction}
      />

      <JudgeCardSection
        title="Documentation"
        subtitle="Evidence and implementation references mapped for scoring criteria."
        cards={DOCUMENTATION_CARDS}
        onCardAction={handleCardAction}
      />

      <JudgeCardSection
        title="Submission Assets"
        subtitle="Repository and delivery artifacts for final capstone review."
        cards={SUBMISSION_ASSETS}
        onCardAction={handleCardAction}
      />

      <section
        className="grid items-stretch gap-4 md:grid-cols-2"
        aria-label="Recommended flow"
        data-testid="judge-flow-section"
      >
        <Card className="h-full" data-testid="judge-flow-card">
          <CardHeader>
            <CardTitle className="text-lg">Recommended Flow</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-2 text-sm">
              {EVALUATION_FLOW.map((step, index) => (
                <li key={step} className="flex items-center gap-3">
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-[var(--primary-soft)] text-xs font-semibold">
                    {index + 1}
                  </span>
                  <span>{step}</span>
                  {index < EVALUATION_FLOW.length - 1 ? (
                    <ArrowRight className="ml-auto h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--text-muted)]" />
                  ) : null}
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>

        <Card className="h-full" data-testid="judge-snapshot-card">
          <CardHeader>
            <CardTitle className="text-lg">Platform Snapshot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-[var(--text-muted)]">
            <p>
              WalletMind is built to demonstrate production-style AI
              architecture with explainable orchestration.
            </p>
            <ul className="space-y-2">
              <li className="flex items-center gap-2">
                <Bot className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--primary)]" />
                Specialized agent ecosystem
              </li>
              <li className="flex items-center gap-2">
                <Boxes className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--primary)]" />
                Deterministic function-tool boundaries
              </li>
              <li className="flex items-center gap-2">
                <CloudCog className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--primary)]" />
                REST + MCP interoperability
              </li>
            </ul>
          </CardContent>
        </Card>
      </section>

      <footer
        className="w-full rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface-soft)] px-4 py-3 text-sm"
        data-testid="judge-footer"
      >
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="font-semibold">WalletMind</p>
            <p className="text-[var(--text-muted)]">
              Google AI Agents Capstone
            </p>
          </div>
          <p className="text-[var(--text-muted)]">
            Version {import.meta.env.VITE_APP_VERSION ?? "0.1.0"}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={() => openInNewTab(PROJECT_ROOT)}
            >
              <FolderGit2 className="mr-1 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              GitHub
            </Button>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={() =>
                openInNewTab(`${PROJECT_ROOT}/blob/main/README.md`)
              }
            >
              <FileText className="mr-1 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              README
            </Button>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={() => openInNewTab(`${PROJECT_ROOT}/blob/main/LICENSE`)}
            >
              <Scale className="mr-1 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              License
            </Button>
          </div>
        </div>
      </footer>

      <Dialog
        open={isComingSoonOpen}
        title="Coming Soon"
        description="This submission asset will be available in the final submission package."
        onClose={() => setIsComingSoonOpen(false)}
        actions={
          <Button
            type="button"
            variant="secondary"
            onClick={() => setIsComingSoonOpen(false)}
          >
            Close
          </Button>
        }
      />
    </div>
  );
}
