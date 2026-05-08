"use client";

import { useEffect, useRef, useState } from "react";
import clsx from "clsx";

import type { Quote } from "@/lib/api-types";

/** 종목 카드용 실시간 가격/등락률 — 변동 시 짧게 깜빡. */
export function LiveQuote({ quote }: { quote: Quote | undefined }) {
  const price = quote?.current_price ?? null;
  const prev = useRef<number | null>(null);
  const [flash, setFlash] = useState<"up" | "down" | null>(null);

  useEffect(() => {
    if (price === null) return;
    if (prev.current !== null && price !== prev.current) {
      setFlash(price > prev.current ? "up" : "down");
      const t = setTimeout(() => setFlash(null), 600);
      prev.current = price;
      return () => clearTimeout(t);
    }
    prev.current = price;
  }, [price]);

  if (!quote || price === null) {
    return (
      <div className="text-[11px] font-mono-jb text-kkj-text-soft px-2 py-1">
        {quote?.error ? "시세 오류" : "시세 …"}
      </div>
    );
  }
  const rate = quote.change_rate ?? 0;
  const colorCls =
    rate > 0
      ? "text-kkj-red"
      : rate < 0
        ? "text-kkj-blue"
        : "text-kkj-text";
  const flashCls =
    flash === "up"
      ? "bg-kkj-red/15"
      : flash === "down"
        ? "bg-kkj-blue/15"
        : "bg-transparent";
  return (
    <div
      className={clsx(
        "flex items-baseline gap-2 px-2 py-1 rounded transition-colors duration-700",
        flashCls,
      )}
    >
      <span className={clsx("font-gmarket-bold text-base", colorCls)}>
        {price.toLocaleString()}
      </span>
      <span className={clsx("text-[11px] font-mono-jb", colorCls)}>
        {rate > 0 ? "+" : ""}
        {rate.toFixed(2)}%
      </span>
    </div>
  );
}
