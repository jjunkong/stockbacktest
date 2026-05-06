"use client";

import {
  ColorType,
  LineSeries,
  createChart,
  type IChartApi,
  type LineData,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useMemo, useRef } from "react";

import type { KospiRow } from "@/lib/api-types";

interface KospiLineChartProps {
  rows: KospiRow[];
  height?: number;
  className?: string;
}

function dateToTime(s: string): UTCTimestamp {
  return Math.floor(new Date(s).getTime() / 1000) as UTCTimestamp;
}

const KKJ = {
  text: "#0F172A",
  textMuted: "#475569",
  border: "#E5E7EB",
  borderSoft: "#F1F5F9",
  card: "#FFFFFF",
  emerald: "#10B981",
  emeraldGlow: "#ECFDF5",
};

export function KospiLineChart({ rows, height = 380, className }: KospiLineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  const closeData = useMemo<LineData[]>(
    () => rows.map((r) => ({ time: dateToTime(r.date), value: r.close })),
    [rows],
  );
  const maData = useMemo<LineData[]>(
    () =>
      rows
        .filter((r) => r.ma !== null)
        .map((r) => ({ time: dateToTime(r.date), value: r.ma as number })),
    [rows],
  );

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: KKJ.card },
        textColor: KKJ.textMuted,
        fontFamily: "'Nanum Gothic', sans-serif",
      },
      grid: {
        vertLines: { color: KKJ.borderSoft },
        horzLines: { color: KKJ.borderSoft },
      },
      rightPriceScale: { borderColor: KKJ.border },
      timeScale: { borderColor: KKJ.border, timeVisible: false },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
      handleScale: {
        mouseWheel: true,
        pinch: true,
        axisPressedMouseMove: { time: true, price: false },
      },
      autoSize: true,
    });

    const closeSeries = chart.addSeries(LineSeries, {
      color: KKJ.text,
      lineWidth: 2,
      title: "코스피",
    });
    closeSeries.setData(closeData);

    if (maData.length > 0) {
      const maSeries = chart.addSeries(LineSeries, {
        color: KKJ.emerald,
        lineWidth: 1,
        lineStyle: 3,
        title: "60일 이평",
      });
      maSeries.setData(maData);
    }

    chart.timeScale().fitContent();
    chartRef.current = chart;
    return () => {
      chart.remove();
      chartRef.current = null;
    };
  }, [closeData, maData]);

  return (
    <div className={className}>
      <div className="kkj-card overflow-hidden">
        <div ref={containerRef} style={{ width: "100%", height }} />
      </div>
    </div>
  );
}
