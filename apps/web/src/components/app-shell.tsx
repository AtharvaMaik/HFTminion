import Link from "next/link";
import { Activity, Database, Radar, ShieldAlert, SlidersHorizontal } from "lucide-react";

const nav = [
  { label: "Overview", href: "/", icon: Activity },
  { label: "Feeds", href: "/feeds/feed-global-news", icon: Database },
  { label: "Incidents", href: "/incidents", icon: ShieldAlert },
  { label: "Replay", href: "/incidents", icon: Radar },
  { label: "Config", href: "/feeds/feed-global-news", icon: SlidersHorizontal },
];

export function AppShell({
  children,
  title,
  eyebrow,
}: {
  children: React.ReactNode;
  title: string;
  eyebrow: string;
}) {
  return (
    <div className="grid min-h-screen grid-cols-1 bg-transparent text-white lg:grid-cols-[240px_1fr]">
      <aside className="border-b border-white/6 bg-[#131b2e]/90 px-6 py-8 lg:border-b-0 lg:border-r">
        <div className="mb-10">
          <div className="text-xs uppercase tracking-[0.34em] text-cyan-200/70">
            HFT Minion
          </div>
          <div className="mt-3 font-[family-name:var(--font-display)] text-2xl font-semibold">
            AltData Reliability OS
          </div>
          <p className="mt-3 max-w-[18rem] text-sm text-white/55">
            Reliability command surface for alternative data feeds, derived features, and operator response.
          </p>
        </div>
        <nav className="space-y-2">
          {nav.map(({ href, icon: Icon, label }) => (
            <Link
              key={href + label}
              href={href}
              className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-white/70 transition-colors hover:bg-cyan-400/8 hover:text-cyan-100"
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
      </aside>

      <main className="grid-glow px-5 py-6 sm:px-8 lg:px-10">
        <div className="mb-8 flex flex-col gap-4 rounded-2xl panel px-6 py-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="text-xs uppercase tracking-[0.32em] text-cyan-200/65">
              {eyebrow}
            </div>
            <h1 className="mt-3 font-[family-name:var(--font-display)] text-3xl font-semibold">
              {title}
            </h1>
          </div>
          <div className="grid gap-3 text-sm text-white/60 md:grid-cols-3">
            <div className="rounded-lg bg-white/4 px-4 py-3">
              <div className="text-xs uppercase tracking-[0.24em] text-white/45">
                Stream state
              </div>
              <div className="mt-2 font-[family-name:var(--font-mono)] text-cyan-100">
                18 feeds / 44 features
              </div>
            </div>
            <div className="rounded-lg bg-white/4 px-4 py-3">
              <div className="text-xs uppercase tracking-[0.24em] text-white/45">
                Active response
              </div>
              <div className="mt-2 font-[family-name:var(--font-mono)] text-orange-100">
                2 incidents under triage
              </div>
            </div>
            <div className="rounded-lg bg-white/4 px-4 py-3">
              <div className="text-xs uppercase tracking-[0.24em] text-white/45">
                Replay window
              </div>
              <div className="mt-2 font-[family-name:var(--font-mono)] text-emerald-100">
                PIT restored at T-4m
              </div>
            </div>
          </div>
        </div>
        {children}
      </main>
    </div>
  );
}

