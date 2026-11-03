import Link from "next/link";
import {
  Activity,
  ArrowRight,
  Camera,
  MessageSquare,
  Ruler,
  ScanLine,
  Sparkles,
  Upload,
} from "lucide-react";
import { loginWithGoogle } from "@/lib/actions/auth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const features = [
  {
    icon: ScanLine,
    title: "Pose overlay",
    description:
      "Every upload is analyzed automatically and returned with a clean skeleton overlay so you can see the exact frame being measured.",
  },
  {
    icon: Ruler,
    title: "Phase-aware joint metrics",
    description:
      "Hip, knee, and ankle angles are compared with reference ranges for toe off, mid stance, and touchdown.",
  },
  {
    icon: MessageSquare,
    title: "AI coaching and chat",
    description:
      "Get concise AI feedback, then ask follow-up questions about cues and drills using only your measured data.",
  },
];

const steps = [
  {
    icon: Upload,
    title: "Upload a frame",
    description: "Pick a sprint photo and choose the phase and direction.",
  },
  {
    icon: Camera,
    title: "Review the analysis",
    description: "Inspect annotated pose, joint angles, and rule-based notes.",
  },
  {
    icon: Sparkles,
    title: "Ask for coaching",
    description: "Generate AI feedback and chat about fixes and drills.",
  },
];

export function Landing() {
  return (
    <main>
      <section className="relative overflow-hidden">
        <div
          aria-hidden="true"
          className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_right,rgba(188,21,69,0.18),transparent_42%),radial-gradient(circle_at_20%_20%,rgba(188,21,69,0.08),transparent_34%)]"
        />
        <div className="mx-auto flex max-w-7xl flex-col items-center px-4 pb-20 pt-16 text-center sm:px-6 sm:pt-24 lg:px-8">
          <Badge
            variant="secondary"
            className="mb-6 gap-1.5 rounded-full border border-primary/15 bg-white/80 px-3 py-1 text-primary shadow-sm"
          >
            <Sparkles className="size-3.5" />
            AI-powered sprint analysis
          </Badge>
          <h1 className="max-w-4xl text-balance text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
            See every stride.
            <span className="block text-primary">Fix the next one.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-pretty text-base leading-7 text-muted-foreground sm:text-lg">
            AGOS turns a single sprint photo into measured joint angles,
            phase-specific feedback, and an AI coach that answers your
            questions. Organize every analysis in folders you control.
          </p>
          <div className="mt-9 flex w-full flex-col items-center justify-center gap-3 sm:w-auto sm:flex-row">
            <form action={loginWithGoogle} className="w-full sm:w-auto">
              <Button
                type="submit"
                size="lg"
                className="h-12 w-full rounded-full px-7 text-base shadow-lg shadow-primary/20 sm:w-auto"
              >
                Continue with Google
                <ArrowRight className="size-4" />
              </Button>
            </form>
            <Button
              asChild
              variant="outline"
              size="lg"
              className="h-12 w-full rounded-full px-7 text-base sm:w-auto"
            >
              <Link href="/library">Browse the library</Link>
            </Button>
          </div>
          <p className="mt-4 text-xs text-muted-foreground">
            No credit card. Your images stay private to your account.
          </p>
        </div>
      </section>

      <section className="mx-auto w-full max-w-7xl px-4 pb-20 sm:px-6 lg:px-8">
        <div className="grid gap-4 md:grid-cols-3">
          {features.map((feature) => (
            <Card
              key={feature.title}
              className="border-border/80 bg-card/90 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <CardHeader>
                <span className="mb-2 flex size-11 items-center justify-center rounded-2xl bg-accent text-primary">
                  <feature.icon className="size-5" aria-hidden="true" />
                </span>
                <CardTitle>{feature.title}</CardTitle>
                <CardDescription className="leading-6">
                  {feature.description}
                </CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      <section className="border-y border-border/70 bg-white/55">
        <div className="mx-auto w-full max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              How it works
            </h2>
            <p className="mt-3 text-muted-foreground">
              Three steps from a phone photo to a more useful training cue.
            </p>
          </div>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {steps.map((step, index) => (
              <Card key={step.title} className="border-border/80 shadow-sm">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <span className="flex size-9 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
                      {index + 1}
                    </span>
                    <step.icon
                      className="size-4 text-muted-foreground"
                      aria-hidden="true"
                    />
                  </div>
                  <h3 className="mt-4 font-semibold">{step.title}</h3>
                  <p className="mt-1 text-sm leading-6 text-muted-foreground">
                    {step.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <footer className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-3 px-4 py-10 text-sm text-muted-foreground sm:flex-row sm:px-6 lg:px-8">
        <span className="flex items-center gap-2 font-semibold text-foreground">
          <Activity className="size-4 text-primary" aria-hidden="true" />
          AGOS
        </span>
        <span>Sprint form analysis, measured and explained.</span>
      </footer>
    </main>
  );
}
