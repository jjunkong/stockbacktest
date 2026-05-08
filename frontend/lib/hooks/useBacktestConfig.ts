"use client";

import { useCallback, useEffect, useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import type {
  ConditionId,
  EntryOption,
  MarketId,
} from "@/lib/api-types";

export interface BacktestConfig {
  cond: ConditionId;
  market: MarketId;
  entry: EntryOption;
  trackDays: number;
  extraDays: number;
  /** 비율 (0.05, 0.10 ...) */
  targets: number[];
  /** API 쿼리/요청용 ("5,10,15,20") */
  targetsCsv: string;
}

// 사용자가 마지막에 선택한 설정 (localStorage)
const LS_KEY = "backtest:user-defaults";

const HARD_DEFAULT: BacktestConfig = {
  cond: "cond1",
  market: "all",
  entry: "open_next",
  trackDays: 10,
  extraDays: 20,
  targets: [0.05, 0.1, 0.15, 0.2],
  targetsCsv: "5,10,15,20",
};

interface UserDefaults {
  cond?: ConditionId;
  market?: MarketId;
  entry?: EntryOption;
  trackDays?: number;
  extraDays?: number;
  targetsCsv?: string;
}

function loadUserDefaults(): UserDefaults {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(LS_KEY);
    return raw ? (JSON.parse(raw) as UserDefaults) : {};
  } catch {
    return {};
  }
}

function saveUserDefaults(patch: UserDefaults): void {
  if (typeof window === "undefined") return;
  try {
    const prev = loadUserDefaults();
    const next = { ...prev, ...patch };
    window.localStorage.setItem(LS_KEY, JSON.stringify(next));
  } catch {
    // ignore quota / private mode
  }
}

/** URL > localStorage > HARD_DEFAULT 순서로 적용 */
function getDefault(): BacktestConfig {
  const ud = loadUserDefaults();
  return {
    ...HARD_DEFAULT,
    ...(ud.cond ? { cond: ud.cond } : {}),
    ...(ud.market ? { market: ud.market } : {}),
    ...(ud.entry ? { entry: ud.entry } : {}),
    ...(ud.trackDays !== undefined ? { trackDays: ud.trackDays } : {}),
    ...(ud.extraDays !== undefined ? { extraDays: ud.extraDays } : {}),
    ...(ud.targetsCsv ? { targetsCsv: ud.targetsCsv, targets: parseTargetsCsv(ud.targetsCsv).targets } : {}),
  };
}

function parseTargetsCsv(csv: string): { targets: number[]; csv: string } {
  const cleaned = csv
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean)
    .map((x) => Number(x))
    .filter((n) => Number.isFinite(n) && n > 0);
  const sorted = Array.from(new Set(cleaned)).sort((a, b) => a - b);
  if (sorted.length === 0) {
    return { targets: DEFAULT.targets, csv: DEFAULT.targetsCsv };
  }
  return {
    targets: sorted.map((n) => n / 100),
    csv: sorted.join(","),
  };
}

/**
 * URL 쿼리 파라미터 기반 백테스트 설정.
 * 어느 페이지에서든 호출하면 같은 설정을 읽고 update 가능.
 */
export function useBacktestConfig() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const config = useMemo<BacktestConfig>(() => {
    const def = getDefault();   // localStorage + HARD_DEFAULT 병합

    const condRaw = params.get("cond");
    const marketRaw = params.get("market");
    const entryRaw = params.get("entry");
    const track = parseInt(params.get("track") ?? "");
    const extra = parseInt(params.get("extra") ?? "");
    const targetsRaw = params.get("targets") ?? "";

    const cond: ConditionId =
      condRaw === "cond1" || condRaw === "cond2" ? condRaw : def.cond;
    const market: MarketId =
      marketRaw === "all" || marketRaw === "KOSPI" || marketRaw === "KOSDAQ"
        ? marketRaw
        : def.market;
    const entry: EntryOption =
      entryRaw === "close_today" || entryRaw === "open_next" || entryRaw === "close_next"
        ? entryRaw
        : def.entry;

    const { targets, csv } = targetsRaw
      ? parseTargetsCsv(targetsRaw)
      : { targets: def.targets, csv: def.targetsCsv };

    return {
      cond,
      market,
      entry,
      trackDays: Number.isFinite(track) && track >= 1 ? track : def.trackDays,
      extraDays: Number.isFinite(extra) && extra >= 0 ? extra : def.extraDays,
      targets,
      targetsCsv: csv,
    };
  }, [params]);

  // 설정이 바뀔 때마다 localStorage에 저장 (다음 방문 시 그대로 복원)
  useEffect(() => {
    saveUserDefaults({
      cond: config.cond,
      market: config.market,
      entry: config.entry,
      trackDays: config.trackDays,
      extraDays: config.extraDays,
      targetsCsv: config.targetsCsv,
    });
  }, [
    config.cond,
    config.market,
    config.entry,
    config.trackDays,
    config.extraDays,
    config.targetsCsv,
  ]);

  const update = useCallback(
    (patch: Partial<BacktestConfig>) => {
      const next = new URLSearchParams(params.toString());

      if (patch.cond !== undefined) next.set("cond", patch.cond);
      if (patch.market !== undefined) next.set("market", patch.market);
      if (patch.entry !== undefined) next.set("entry", patch.entry);
      if (patch.trackDays !== undefined) next.set("track", String(patch.trackDays));
      if (patch.extraDays !== undefined) next.set("extra", String(patch.extraDays));

      // targets는 csv 또는 number[] 둘 다 지원
      if (patch.targetsCsv !== undefined) {
        const { csv } = parseTargetsCsv(patch.targetsCsv);
        next.set("targets", csv);
      } else if (patch.targets !== undefined) {
        const csv = patch.targets.map((t) => Math.round(t * 100)).join(",");
        next.set("targets", csv);
      }

      router.replace(`${pathname}?${next.toString()}`, { scroll: false });
    },
    [params, pathname, router],
  );

  return { config, update };
}
