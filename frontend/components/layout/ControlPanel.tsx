"use client";

import clsx from "clsx";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { SectionLabel } from "@/components/ui";
import { api } from "@/lib/api";
import { useBacktestConfig } from "@/lib/hooks/useBacktestConfig";
import type { ConditionId, EntryOption, MarketId } from "@/lib/api-types";

// fallback - 백엔드 응답 없을 때만 사용
const FALLBACK_CONDITIONS: { id: ConditionId; label: string }[] = [
  { id: "cond1", label: "급등주 추격형" },
  { id: "cond2", label: "갭상승 정배열형" },
];

const MARKETS: { id: MarketId; label: string }[] = [
  { id: "all", label: "전체" },
  { id: "KOSPI", label: "KOSPI" },
  { id: "KOSDAQ", label: "KOSDAQ" },
];

const ENTRIES: { id: EntryOption; label: string; sub: string }[] = [
  { id: "close_today", label: "당일 종가", sub: "신호 발생일 종가" },
  { id: "open_next", label: "다음날 시가", sub: "현실적 (기본값)" },
  { id: "close_next", label: "다음날 종가", sub: "하루 관망" },
];

const FIELD_LABEL_CLASS =
  "block text-[11px] font-bold uppercase tracking-[0.08em] text-kkj-text-muted mb-1.5";

const SELECT_CLASS =
  "w-full rounded-lg border border-kkj-border bg-kkj-card px-3 py-2 text-sm text-kkj-text kkj-focus hover:border-kkj-emerald transition-colors";

/**
 * 사이드바 백테스트 설정 컨트롤. URL 쿼리에 동기화.
 */
export function ControlPanel() {
  const { config, update } = useBacktestConfig();

  const [targetsInput, setTargetsInput] = useState(config.targetsCsv);
  useEffect(() => setTargetsInput(config.targetsCsv), [config.targetsCsv]);

  const conditionsQ = useQuery({
    queryKey: ["conditions"],
    queryFn: () => api.conditions(),
    staleTime: 5 * 60 * 1000, // 5분
  });
  const conditions = conditionsQ.data ?? FALLBACK_CONDITIONS;

  return (
    <div className="space-y-4">
      <SectionLabel>설정</SectionLabel>

      {/* 조건식 */}
      <div>
        <label className={FIELD_LABEL_CLASS}>조건식</label>
        <select
          value={config.cond}
          onChange={(e) => update({ cond: e.target.value as ConditionId })}
          className={SELECT_CLASS}
        >
          {conditions.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      {/* 시장 */}
      <div>
        <label className={FIELD_LABEL_CLASS}>시장</label>
        <div className="grid grid-cols-3 gap-1">
          {MARKETS.map((m) => {
            const active = config.market === m.id;
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => update({ market: m.id })}
                className={clsx(
                  "rounded-md text-xs font-medium py-1.5 transition-colors kkj-focus",
                  active
                    ? "bg-kkj-emerald text-white"
                    : "bg-kkj-card-soft text-kkj-text-muted hover:bg-kkj-emerald-glow hover:text-kkj-emerald-strong",
                )}
              >
                {m.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* 진입가 */}
      <div>
        <label className={FIELD_LABEL_CLASS}>진입가</label>
        <select
          value={config.entry}
          onChange={(e) => update({ entry: e.target.value as EntryOption })}
          className={SELECT_CLASS}
        >
          {ENTRIES.map((e) => (
            <option key={e.id} value={e.id}>
              {e.label} · {e.sub}
            </option>
          ))}
        </select>
      </div>

      {/* 추적 기간 */}
      <div>
        <label className={FIELD_LABEL_CLASS}>
          추적 기간{" "}
          <span className="font-mono-jb text-kkj-emerald-strong">{config.trackDays}일</span>
        </label>
        <input
          type="range"
          min={5}
          max={20}
          step={1}
          value={config.trackDays}
          onChange={(e) => update({ trackDays: parseInt(e.target.value) })}
          className="w-full accent-kkj-emerald cursor-pointer"
        />
      </div>

      {/* 초과 추적 */}
      <div>
        <label className={FIELD_LABEL_CLASS}>
          초과 추적{" "}
          <span className="font-mono-jb text-kkj-emerald-strong">+{config.extraDays}일</span>
        </label>
        <input
          type="range"
          min={0}
          max={30}
          step={5}
          value={config.extraDays}
          onChange={(e) => update({ extraDays: parseInt(e.target.value) })}
          className="w-full accent-kkj-emerald cursor-pointer"
        />
      </div>

      {/* 목표 수익률 */}
      <div>
        <label className={FIELD_LABEL_CLASS}>목표 수익률 (%)</label>
        <input
          type="text"
          value={targetsInput}
          onChange={(e) => setTargetsInput(e.target.value)}
          onBlur={() => {
            if (targetsInput !== config.targetsCsv) {
              update({ targetsCsv: targetsInput });
            }
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") (e.target as HTMLInputElement).blur();
          }}
          placeholder="5,10,15,20"
          className={`${SELECT_CLASS} font-mono-jb`}
        />
        <p className="mt-1.5 text-[11px] text-kkj-text-soft">
          쉼표로 구분. 예: 5,10,15,20
        </p>
      </div>
    </div>
  );
}
