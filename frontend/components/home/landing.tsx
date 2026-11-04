import { ArrowRight } from "lucide-react";
import { loginWithGoogle } from "@/lib/actions/auth";
import { PosePreview } from "@/components/pose-preview";
import { Button } from "@/components/ui/button";

const steps = [
  {
    title: "Upload a frame",
    description:
      "Choose a sprint photo, then set the phase and running direction.",
  },
  {
    title: "Read the angles",
    description:
      "Review the pose overlay and the hip, knee, and ankle angles for each leg.",
  },
  {
    title: "Ask AI",
    description:
      "Get AI feedback on the frame and ask about cues and drills. Only your measurements are used.",
  },
];

// Mirrors RANGES in backend/services/analysis.py.
const ranges = [
  { phase: "Toe off", leg: "Swing", hip: "97–113", knee: "58–80", ankle: "96–104" },
  { phase: "Toe off", leg: "Stance", hip: "193–204", knee: "138–155", ankle: "110–147" },
  { phase: "Mid stance", leg: "Swing", hip: "126–146", knee: "26–41", ankle: "108–132" },
  { phase: "Mid stance", leg: "Stance", hip: "155–165", knee: "141–149", ankle: "79–88" },
  { phase: "Touchdown", leg: "Swing", hip: "157–168", knee: "39–49", ankle: "116–130" },
  { phase: "Touchdown", leg: "Stance", hip: "141–152", knee: "146–156", ankle: "97–105" },
];

export function Landing() {
  return (
    <>
      <section className="border-b border-border">
        <div className="mx-auto grid max-w-screen-2xl items-center gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:gap-16 lg:px-8 lg:py-20">
          <div>
            <p className="label-caps text-primary">Sprint form analysis</p>
            <h1 className="display-type mt-3 text-6xl sm:text-7xl xl:text-8xl">
              Sprint mechanics,
              <span className="block text-primary">measured.</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-7 text-muted-foreground">
              Upload a sprint frame. ĀGOS measures hip, knee, and ankle angles
              and checks them against reference ranges for toe off, mid stance,
              and touchdown.
            </p>
            <div className="mt-8 flex flex-col gap-2 sm:flex-row">
              <form action={loginWithGoogle} className="w-full sm:w-auto">
                <Button type="submit" size="lg" className="w-full sm:w-auto">
                  Continue with Google
                  <ArrowRight className="size-4" />
                </Button>
              </form>
              <Button
                asChild
                variant="outline"
                size="lg"
                className="w-full sm:w-auto"
              >
                <a href="#ranges">View reference ranges</a>
              </Button>
            </div>
          </div>
          <div className="mx-auto w-full max-w-xl lg:mr-0">
            <PosePreview />
          </div>
        </div>
      </section>

      <section className="bg-primary text-primary-foreground">
        <ol className="mx-auto grid max-w-screen-2xl px-4 sm:px-6 md:grid-cols-3 lg:px-8">
          {steps.map((step, index) => (
            <li
              key={step.title}
              className="border-b border-white/25 py-8 last:border-b-0 md:border-b-0 md:border-l md:px-6 md:first:border-l-0 md:first:pl-0 md:last:pr-0"
            >
              <span className="font-display text-5xl font-extrabold italic leading-none text-white/60 tabular-nums">
                0{index + 1}
              </span>
              <h2 className="display-type mt-3 text-3xl">{step.title}</h2>
              <p className="mt-2 max-w-md text-base leading-6 text-white/85">
                {step.description}
              </p>
            </li>
          ))}
        </ol>
      </section>

      <section
        id="ranges"
        className="mx-auto max-w-screen-2xl scroll-mt-[70px] px-4 py-12 sm:px-6 lg:px-8 lg:py-16"
      >
        <p className="label-caps text-primary">Reference ranges</p>
        <h2 className="display-type mt-2 text-4xl sm:text-5xl">
          What each frame is measured against
        </h2>
        <p className="mt-3 max-w-2xl text-base text-muted-foreground">
          All angles in degrees. ĀGOS works out which leg is swing and which is
          stance. Touchdown also checks thigh separation, 7–28°.
        </p>
        <div className="mt-8 overflow-x-auto rounded-lg border border-border bg-card">
          <table className="w-full min-w-[520px] text-left text-sm tabular-nums">
            <thead className="border-b border-border">
              <tr>
                {["Phase", "Leg", "Hip", "Knee", "Ankle"].map((heading) => (
                  <th
                    key={heading}
                    scope="col"
                    className="label-caps px-4 py-3 text-muted-foreground"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {ranges.map((row) => (
                <tr key={`${row.phase}-${row.leg}`}>
                  <td className="px-4 py-3 font-semibold">{row.phase}</td>
                  <td className="px-4 py-3 text-muted-foreground">{row.leg}</td>
                  <td className="px-4 py-3">{row.hip}</td>
                  <td className="px-4 py-3">{row.knee}</td>
                  <td className="px-4 py-3">{row.ankle}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
