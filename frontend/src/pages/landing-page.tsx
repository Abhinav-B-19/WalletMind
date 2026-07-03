import { Link } from "react-router-dom";
import {
  BrainCircuit,
  Bot,
  ChartColumnBig,
  CheckCircle2,
  Database,
  FileSearch,
  FileUp,
  Gauge,
  Layers,
  PieChart,
  ShieldCheck,
  Sparkles,
  Wallet,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageTitle, SectionTitle } from "@/components/ui/section-title";

const AI_CAPABILITIES = [
  {
    title: "Statement Parsing",
    description:
      "Extracts financial data from PDF, CSV, XLSX, and image statements.",
    icon: FileUp,
  },
  {
    title: "Transaction Intelligence",
    description:
      "Normalizes, enriches, and classifies transactions with deterministic rules.",
    icon: FileSearch,
  },
  {
    title: "Spending Insights",
    description:
      "Surfaces merchant trends, category distribution, and recurring signals.",
    icon: PieChart,
  },
  {
    title: "Financial Health Score",
    description:
      "Combines five score components into a transparent health grade.",
    icon: Gauge,
  },
  {
    title: "AI Assistant",
    description:
      "Ask grounded questions and get answer traces from statement transactions.",
    icon: Bot,
  },
  {
    title: "Budget Recommendations",
    description:
      "Builds deterministic budgets and prioritized monthly savings opportunities.",
    icon: Wallet,
  },
  {
    title: "Monthly Financial Report",
    description:
      "Generates advisor-style monthly intelligence with risks and action plans.",
    icon: ChartColumnBig,
  },
];

const WORKFLOW_STEPS = [
  "Upload",
  "AI Processing",
  "Insights",
  "Recommendations",
  "Financial Intelligence",
];

const SHOWCASE_ITEMS = [
  "AI Dashboard",
  "Transactions",
  "Health Score",
  "AI Assistant",
  "Monthly Report",
];

const TECH_STACK = [
  "React",
  "FastAPI",
  "Gemini",
  "SQLAlchemy",
  "React Query",
  "Tailwind",
];

const ARCHITECTURE_HIGHLIGHTS = [
  {
    title: "Parser",
    description: "Ingests statement files into structured transaction records.",
    icon: FileUp,
  },
  {
    title: "Normalizer",
    description: "Standardizes amount, type, merchant, and category fields.",
    icon: Layers,
  },
  {
    title: "Intelligence Engine",
    description:
      "Applies deterministic financial computations and risk heuristics.",
    icon: BrainCircuit,
  },
  {
    title: "Gemini Reasoning Layer",
    description:
      "Adds narrative explanations and action guidance over grounded data.",
    icon: Sparkles,
  },
];

const WHY_WALLETMIND = [
  "AI-first workflow with grounded transaction evidence.",
  "Deterministic financial calculations for transparent outputs.",
  "Clear reasoning with measurable recommendations.",
  "Production-ready architecture that scales from demo to product.",
];

export function HomePage() {
  return (
    <div className="space-y-8" aria-label="WalletMind landing page">
      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-stretch">
        <Card className="overflow-hidden border-[#4f8df7]/30 bg-[linear-gradient(145deg,rgba(79,141,247,0.18),rgba(18,31,52,0.82))]">
          <CardContent className="space-y-6 p-7 md:p-8">
            <PageTitle
              title="WalletMind"
              subtitle="AI Financial Intelligence Platform"
            />
            <div className="space-y-3">
              <p className="text-3xl font-semibold tracking-tight md:text-4xl">
                Understand your money in under a minute with grounded AI
                insights.
              </p>
              <p className="max-w-3xl text-sm leading-relaxed text-[var(--text-muted)] md:text-base">
                WalletMind transforms raw bank statements into clear financial
                intelligence: transaction enrichment, health scoring, spending
                insights, budget recommendations, assistant guidance, and
                advisor-style monthly reports.
              </p>
            </div>

            <div
              className="flex flex-wrap gap-3"
              aria-label="Landing primary actions"
            >
              <Button asChild>
                <Link to="/register">Get Started</Link>
              </Button>
              <Button asChild variant="secondary">
                <Link to="/login">Open Workspace</Link>
              </Button>
            </div>

            <div
              className="grid gap-3 text-sm sm:grid-cols-2"
              aria-label="Landing value bullets"
            >
              <div className="inline-flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]/70 px-3 py-2">
                <ShieldCheck className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[#29d0b3]" />
                Deterministic + AI reasoning
              </div>
              <div className="inline-flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]/70 px-3 py-2">
                <Database className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[#4f8df7]" />
                Statement-grounded answers
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="text-lg">Product Preview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-4">
              <p className="text-sm font-semibold">Advisor-Grade Snapshot</p>
              <p className="text-xs text-[var(--text-muted)]">
                Health, risk, and action plan in one unified monthly narrative.
              </p>
            </div>

            <div className="grid gap-2 sm:grid-cols-2">
              {["Health Score", "Insights", "Budget", "Assistant"].map(
                (item) => (
                  <div
                    key={item}
                    className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 text-xs text-[var(--text-muted)]"
                  >
                    {item}
                  </div>
                ),
              )}
            </div>

            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-4 text-xs text-[var(--text-muted)]">
              Dashboard preview placeholder
              <div className="mt-3 h-28 rounded-[var(--radius-sm)] border border-dashed border-[var(--border)] bg-[var(--surface)]" />
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <SectionTitle
          title="AI Capabilities"
          subtitle="Everything needed to move from statement files to confident financial decisions."
        />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {AI_CAPABILITIES.map(({ title, description, icon: Icon }) => (
            <Card key={title} className="h-full">
              <CardContent className="space-y-3 p-5">
                <div className="inline-flex items-center rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-2.5 py-2">
                  <Icon className="h-[var(--icon-md)] w-[var(--icon-md)] text-[var(--primary)]" />
                </div>
                <h3 className="text-base font-semibold">{title}</h3>
                <p className="text-sm text-[var(--text-muted)]">
                  {description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <SectionTitle
          title="How It Works"
          subtitle="A clear product flow from data ingestion to intelligent financial action."
        />
        <Card>
          <CardContent className="p-5">
            <div
              className="grid gap-2 md:grid-cols-5 md:items-center"
              aria-label="WalletMind workflow"
            >
              {WORKFLOW_STEPS.map((step, index) => (
                <div key={step} className="flex items-center gap-2">
                  <div className="grid h-7 w-7 place-items-center rounded-full bg-[var(--primary-soft)] text-xs font-semibold text-[var(--text)]">
                    {index + 1}
                  </div>
                  <span className="text-sm">{step}</span>
                  {index < WORKFLOW_STEPS.length - 1 ? (
                    <Sparkles className="ml-auto hidden h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--text-muted)] md:block" />
                  ) : null}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <SectionTitle
          title="Feature Showcase"
          subtitle="Core product surfaces judges and users can evaluate instantly."
        />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {SHOWCASE_ITEMS.map((item) => (
            <Card key={item}>
              <CardContent className="space-y-2 p-4">
                <p className="text-sm font-semibold">{item}</p>
                <div className="h-24 rounded-[var(--radius-sm)] border border-dashed border-[var(--border)] bg-[var(--surface-soft)]" />
                <p className="text-xs text-[var(--text-muted)]">
                  Screenshot placeholder
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Technology</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 sm:grid-cols-2">
            {TECH_STACK.map((item) => (
              <div
                key={item}
                className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] px-3 py-2 text-sm"
              >
                {item}
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Architecture Highlights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {ARCHITECTURE_HIGHLIGHTS.map(
              ({ title, description, icon: Icon }) => (
                <div
                  key={title}
                  className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3"
                >
                  <p className="inline-flex items-center gap-2 text-sm font-semibold">
                    <Icon className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--primary)]" />
                    {title}
                  </p>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">
                    {description}
                  </p>
                </div>
              ),
            )}
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <SectionTitle
          title="Why WalletMind"
          subtitle="Built for transparent financial intelligence instead of black-box guesswork."
        />
        <Card>
          <CardContent
            className="grid gap-3 p-5 md:grid-cols-2"
            aria-label="Why WalletMind advantages"
          >
            {WHY_WALLETMIND.map((item) => (
              <div
                key={item}
                className="inline-flex items-center gap-2 text-sm"
              >
                <CheckCircle2 className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[#29d0b3]" />
                {item}
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
