"use client";

import { useEffect, useRef } from "react";

import {
  AreaSeries,
  ColorType,
  createChart,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";

type ReliabilityChartProps = {
  data: Array<[string, number]>;
};

export function ReliabilityChart({ data }: ReliabilityChartProps) {
  const chartRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!chartRef.current) {
      return;
    }

    const chart: IChartApi = createChart(chartRef.current, {
      autoSize: true,
      height: 280,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#8fa0b8",
      },
      grid: {
        vertLines: { color: "rgba(133, 147, 153, 0.08)" },
        horzLines: { color: "rgba(133, 147, 153, 0.08)" },
      },
      rightPriceScale: {
        borderVisible: false,
      },
      timeScale: {
        borderVisible: false,
      },
    });

    const series = chart.addSeries(AreaSeries, {
      topColor: "rgba(0, 209, 255, 0.28)",
      bottomColor: "rgba(0, 209, 255, 0.02)",
      lineColor: "#4cd6ff",
      lineWidth: 2,
    });

    series.setData(
      data.map(([, value], index) => ({
        time: (index + 1) as UTCTimestamp,
        value,
      }))
    );

    return () => chart.remove();
  }, [data]);

  return <div ref={chartRef} className="h-[280px] w-full" />;
}
