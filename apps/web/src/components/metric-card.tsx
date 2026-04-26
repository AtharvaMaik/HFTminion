import { ArrowDownRight, ArrowUpRight, Dot } from "lucide-react";

type MetricCardProps = {
  label: string;
  value: string;
  delta: string;
  tone: "cyan" | "emerald" | "amber" | "red";
};

const toneStyles: Record<MetricCardProps["tone"], string> = {
  cyan: "from-cyan-400/20 to-cyan-300/5 text-cyan-100",
  emerald: "from-emerald-400/20 to-emerald-300/5 text-emerald-100",
  amber: "from-orange-300/20 to-orange-200/5 text-orange-100",
  red: "from-rose-400/20 to-rose-300/5 text-rose-100",
};

export function MetricCard({ label, value, delta, tone }: MetricCardProps) {
  const positive = !delta.startsWith("-");
  const Icon = positive ? ArrowUpRight : ArrowDownRight;

  return (
    <div className={`panel rounded-xl bg-gradient-to-br ${toneStyles[tone]} p-4`}>
      <div className="mb-6 flex items-center justify-between">
        <span className="text-xs uppercase tracking-[0.28em] text-white/55">
          {label}
        </span>
        <Dot className="h-6 w-6 opacity-70" />
      </div>
      <div className="font-[family-name:var(--font-display)] text-4xl font-semibold">
        {value}
      </div>
      <div className="mt-3 flex items-center gap-2 text-sm text-white/65">
        <Icon className="h-4 w-4" />
        <span>{delta}</span>
      </div>
    </div>
  );
}

