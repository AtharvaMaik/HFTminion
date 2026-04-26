type ReliabilityChartProps = {
  data: Array<[string, number]>;
};

const CHART_WIDTH = 760;
const CHART_HEIGHT = 280;
const CHART_PADDING = {
  top: 24,
  right: 20,
  bottom: 36,
  left: 40,
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function buildPath(points: Array<{ x: number; y: number }>) {
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
}

export function ReliabilityChart({ data }: ReliabilityChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-[280px] items-center justify-center rounded-xl bg-white/3 text-sm text-white/45">
        No trust history available.
      </div>
    );
  }

  const values = data.map(([, value]) => value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const range = Math.max(1, maxValue - minValue);
  const innerWidth = CHART_WIDTH - CHART_PADDING.left - CHART_PADDING.right;
  const innerHeight = CHART_HEIGHT - CHART_PADDING.top - CHART_PADDING.bottom;

  const points = data.map(([time, value], index) => {
    const x =
      CHART_PADDING.left +
      (data.length === 1 ? innerWidth / 2 : (index / (data.length - 1)) * innerWidth);
    const normalized = (value - minValue) / range;
    const y = CHART_PADDING.top + innerHeight - normalized * innerHeight;

    return {
      label: time,
      value,
      x: clamp(x, CHART_PADDING.left, CHART_WIDTH - CHART_PADDING.right),
      y: clamp(y, CHART_PADDING.top, CHART_HEIGHT - CHART_PADDING.bottom),
    };
  });

  const linePath = buildPath(points);
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${
    CHART_HEIGHT - CHART_PADDING.bottom
  } L ${points[0].x} ${CHART_HEIGHT - CHART_PADDING.bottom} Z`;
  const yTicks = [minValue, minValue + range / 2, maxValue].map((value) => Math.round(value));

  return (
    <div className="relative h-[280px] w-full overflow-hidden rounded-xl bg-white/[0.02]">
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        className="h-full w-full"
        role="img"
        aria-label="Weighted trust score trend over the last 24 hours"
      >
        <defs>
          <linearGradient id="trustAreaFill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="rgba(76,214,255,0.45)" />
            <stop offset="100%" stopColor="rgba(76,214,255,0.04)" />
          </linearGradient>
        </defs>

        {yTicks.map((tick) => {
          const y =
            CHART_PADDING.top +
            innerHeight -
            ((tick - minValue) / Math.max(range, 1)) * innerHeight;

          return (
            <g key={tick}>
              <line
                x1={CHART_PADDING.left}
                x2={CHART_WIDTH - CHART_PADDING.right}
                y1={y}
                y2={y}
                stroke="rgba(133, 147, 153, 0.12)"
                strokeDasharray="3 6"
              />
              <text
                x={8}
                y={y + 4}
                fill="rgba(218, 226, 253, 0.55)"
                fontSize="12"
                fontFamily="var(--font-mono-ui)"
              >
                {tick}
              </text>
            </g>
          );
        })}

        <path d={areaPath} fill="url(#trustAreaFill)" />
        <path
          d={linePath}
          fill="none"
          stroke="#4cd6ff"
          strokeWidth="3"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {points.map((point) => (
          <g key={`${point.label}-${point.value}`}>
            <circle cx={point.x} cy={point.y} r="4.5" fill="#0b1326" stroke="#4cd6ff" strokeWidth="2" />
            <text
              x={point.x}
              y={CHART_HEIGHT - 12}
              textAnchor="middle"
              fill="rgba(218, 226, 253, 0.55)"
              fontSize="11"
              fontFamily="var(--font-mono-ui)"
            >
              {point.label}
            </text>
          </g>
        ))}
      </svg>

      <div className="pointer-events-none absolute right-4 top-4 rounded-full border border-cyan-300/15 bg-cyan-400/8 px-3 py-1 font-[family-name:var(--font-mono)] text-xs text-cyan-100">
        {values.at(-1)} latest
      </div>
    </div>
  );
}

