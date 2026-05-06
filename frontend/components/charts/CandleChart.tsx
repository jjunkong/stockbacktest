"use client";

import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  LineSeries,
  LineStyle,
  createChart,
  createSeriesMarkers,
  type CandlestickData,
  type IChartApi,
  type ISeriesApi,
  type ISeriesMarkersPluginApi,
  type LineData,
  type SeriesMarker,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useMemo, useRef, useState } from "react";

import type { OHLCVRow } from "@/lib/api-types";

interface SignalMarker {
  date: string;
  label?: string;
}

interface CandleChartProps {
  rows: OHLCVRow[];
  signals?: SignalMarker[];
  entryPrice?: number | null;
  /** 비율 (0.05 = +5%) */
  targets?: number[];
  height?: number;
  className?: string;
  /** 진입가 표시 라벨 */
  entryLabel?: string;
}

const KKJ = {
  emerald: "#10B981",
  emeraldStrong: "#059669",
  amber: "#F59E0B",
  red: "#EF4444",
  blue: "#3B82F6",
  purple: "#8B5CF6",
  cyan: "#06B6D4",
  text: "#0F172A",
  textMuted: "#475569",
  textSoft: "#94A3B8",
  border: "#E5E7EB",
  borderSoft: "#F1F5F9",
  card: "#FFFFFF",
};

// 이동평균선 컬러 — 캔들/신호 마커와 충돌 안 나게
const MA_COLORS = {
  ma20: KKJ.amber,    // 단기 — 주황
  ma120: KKJ.purple,  // 중기 — 보라
  ma240: KKJ.cyan,    // 장기 — 사이안
};

function dateToTime(s: string): UTCTimestamp {
  return Math.floor(new Date(s).getTime() / 1000) as UTCTimestamp;
}

function formatNumber(n: number): string {
  return n.toLocaleString("ko-KR", { maximumFractionDigits: 0 });
}

function weekdayKor(d: Date): string {
  return ["일", "월", "화", "수", "목", "금", "토"][d.getDay()];
}

/** 단순이동평균 (SMA). 첫 period-1 일은 데이터 없음 → 그 이후만 반환. */
function sma(rows: OHLCVRow[], period: number): LineData[] {
  if (rows.length < period) return [];
  const out: LineData[] = [];
  let sum = 0;
  for (let i = 0; i < rows.length; i++) {
    sum += rows[i].close;
    if (i >= period) sum -= rows[i - period].close;
    if (i >= period - 1) {
      out.push({ time: dateToTime(rows[i].date), value: sum / period });
    }
  }
  return out;
}

/**
 * 한국 주식 일봉 캔들차트.
 * - 양봉=빨강, 음봉=파랑 (한국식)
 * - MA20/120/240 이동평균선 색깔별로 표시
 * - 휠 줌은 X축만 (Y축 자동)
 * - 신호일 마커, 진입가/목표가 가격 라인
 * - 호버 시 좌상단 OHLCV + 등락률 툴팁
 */
export function CandleChart({
  rows,
  signals = [],
  entryPrice,
  targets = [],
  height = 480,
  className,
  entryLabel,
}: CandleChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const ma20Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const ma120Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const ma240Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const markersRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);

  const [hoverInfo, setHoverInfo] = useState<{
    date: string;
    weekday: string;
    o: number;
    h: number;
    l: number;
    c: number;
    v: number;
    change: number | null;
  } | null>(null);

  const candleData = useMemo<CandlestickData[]>(
    () =>
      rows.map((r) => ({
        time: dateToTime(r.date),
        open: r.open,
        high: r.high,
        low: r.low,
        close: r.close,
      })),
    [rows],
  );

  const ma20Data = useMemo(() => sma(rows, 20), [rows]);
  const ma120Data = useMemo(() => sma(rows, 120), [rows]);
  const ma240Data = useMemo(() => sma(rows, 240), [rows]);

  // 차트 + 시리즈 생성 (1회)
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
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: KKJ.emerald, width: 1, style: LineStyle.Dotted, labelBackgroundColor: KKJ.emerald },
        horzLine: { color: KKJ.emerald, width: 1, style: LineStyle.Dotted, labelBackgroundColor: KKJ.emerald },
      },
      rightPriceScale: { borderColor: KKJ.border },
      timeScale: { borderColor: KKJ.border, timeVisible: false, secondsVisible: false },
      handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
      handleScale: {
        mouseWheel: true,
        pinch: true,
        axisPressedMouseMove: { time: true, price: false },
        axisDoubleClickReset: { time: true, price: true },
      },
      autoSize: true,
    });

    const candle = chart.addSeries(CandlestickSeries, {
      upColor: KKJ.red,
      downColor: KKJ.blue,
      borderUpColor: KKJ.red,
      borderDownColor: KKJ.blue,
      wickUpColor: KKJ.red,
      wickDownColor: KKJ.blue,
    });

    const ma20 = chart.addSeries(LineSeries, {
      color: MA_COLORS.ma20,
      lineWidth: 1,
      title: "MA20",
      priceLineVisible: false,
      lastValueVisible: false,
    });
    const ma120 = chart.addSeries(LineSeries, {
      color: MA_COLORS.ma120,
      lineWidth: 1,
      title: "MA120",
      priceLineVisible: false,
      lastValueVisible: false,
    });
    const ma240 = chart.addSeries(LineSeries, {
      color: MA_COLORS.ma240,
      lineWidth: 1,
      title: "MA240",
      priceLineVisible: false,
      lastValueVisible: false,
    });

    chartRef.current = chart;
    candleRef.current = candle;
    ma20Ref.current = ma20;
    ma120Ref.current = ma120;
    ma240Ref.current = ma240;
    // 마커 플러그인 — v5에서 분리됨
    markersRef.current = createSeriesMarkers(candle, []);

    return () => {
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      ma20Ref.current = null;
      ma120Ref.current = null;
      ma240Ref.current = null;
      markersRef.current = null;
    };
  }, []);

  // 데이터/마커/라인 갱신
  useEffect(() => {
    const chart = chartRef.current;
    const candle = candleRef.current;
    if (!chart || !candle) return;

    candle.setData(candleData);
    ma20Ref.current?.setData(ma20Data);
    ma120Ref.current?.setData(ma120Data);
    ma240Ref.current?.setData(ma240Data);

    // 신호 마커
    const markers: SeriesMarker<Time>[] = signals
      .filter((s) => candleData.some((c) => c.time === dateToTime(s.date)))
      .map((s) => ({
        time: dateToTime(s.date),
        position: "aboveBar" as const,
        color: KKJ.amber,
        shape: "arrowDown" as const,
        text: s.label ?? "신호",
      }));
    markersRef.current?.setMarkers(markers);

    // 진입가/목표가 가격 라인
    const lines: ReturnType<typeof candle.createPriceLine>[] = [];
    if (entryPrice && entryPrice > 0) {
      lines.push(
        candle.createPriceLine({
          price: entryPrice,
          color: KKJ.text,
          lineWidth: 1,
          lineStyle: LineStyle.Dotted,
          axisLabelVisible: true,
          title: entryLabel ?? `진입가 ${formatNumber(entryPrice)}`,
        }),
      );
      for (const t of targets) {
        lines.push(
          candle.createPriceLine({
            price: entryPrice * (1 + t),
            color: KKJ.emerald,
            lineWidth: 1,
            lineStyle: LineStyle.Dashed,
            axisLabelVisible: true,
            title: `+${Math.round(t * 100)}%`,
          }),
        );
      }
    }

    chart.timeScale().fitContent();

    // 호버
    const onCrosshair = (param: Parameters<Parameters<IChartApi["subscribeCrosshairMove"]>[0]>[0]) => {
      if (!param.time || !candleRef.current) {
        setHoverInfo(null);
        return;
      }
      const data = param.seriesData.get(candleRef.current) as
        | CandlestickData
        | undefined;
      if (!data) {
        setHoverInfo(null);
        return;
      }
      const ts = (data.time as number) * 1000;
      const dt = new Date(ts);
      const dateStr = dt.toISOString().slice(0, 10);
      const original = rows.find((r) => r.date === dateStr);
      setHoverInfo({
        date: dateStr,
        weekday: weekdayKor(dt),
        o: data.open,
        h: data.high,
        l: data.low,
        c: data.close,
        v: original?.volume ?? 0,
        change: original?.change_rate ?? null,
      });
    };
    chart.subscribeCrosshairMove(onCrosshair);

    return () => {
      chart.unsubscribeCrosshairMove(onCrosshair);
      lines.forEach((l) => candle.removePriceLine(l));
    };
  }, [candleData, ma20Data, ma120Data, ma240Data, rows, signals, entryPrice, targets, entryLabel]);

  return (
    <div className={className}>
      <div className="relative kkj-card overflow-hidden">
        <div ref={containerRef} style={{ width: "100%", height }} />

        {/* 좌상단 호버 툴팁 */}
        {hoverInfo && (
          <div
            className="absolute top-3 left-3 pointer-events-none rounded-lg
                       bg-kkj-card/95 backdrop-blur border border-kkj-border
                       px-3 py-2 text-xs font-mono-jb shadow-md z-10"
          >
            <div className="font-gmarket-bold text-kkj-text mb-1">
              {hoverInfo.date}{" "}
              <span className="text-kkj-text-soft">({hoverInfo.weekday})</span>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-kkj-text-muted">
              <div>시가</div>
              <div className="text-right text-kkj-text">{formatNumber(hoverInfo.o)}</div>
              <div>고가</div>
              <div className="text-right text-kkj-text">{formatNumber(hoverInfo.h)}</div>
              <div>저가</div>
              <div className="text-right text-kkj-text">{formatNumber(hoverInfo.l)}</div>
              <div>종가</div>
              <div className="text-right text-kkj-text">{formatNumber(hoverInfo.c)}</div>
              <div>거래량</div>
              <div className="text-right text-kkj-text">{formatNumber(hoverInfo.v)}</div>
              <div>등락률</div>
              <div
                className={`text-right ${
                  hoverInfo.change === null
                    ? "text-kkj-text"
                    : hoverInfo.change >= 0
                      ? "text-kkj-red"
                      : "text-kkj-blue"
                }`}
              >
                {hoverInfo.change === null
                  ? "-"
                  : `${hoverInfo.change >= 0 ? "+" : ""}${(hoverInfo.change * 100).toFixed(2)}%`}
              </div>
            </div>
          </div>
        )}

        {/* MA 범례 */}
        <div className="absolute top-3 right-3 flex items-center gap-3 rounded-lg bg-kkj-card/95 backdrop-blur border border-kkj-border px-3 py-1.5 text-[11px] font-mono-jb shadow-md z-10">
          <span className="flex items-center gap-1">
            <span className="block w-3 h-0.5" style={{ background: MA_COLORS.ma20 }} />
            MA20
          </span>
          <span className="flex items-center gap-1">
            <span className="block w-3 h-0.5" style={{ background: MA_COLORS.ma120 }} />
            MA120
          </span>
          <span className="flex items-center gap-1">
            <span className="block w-3 h-0.5" style={{ background: MA_COLORS.ma240 }} />
            MA240
          </span>
        </div>
      </div>
    </div>
  );
}
