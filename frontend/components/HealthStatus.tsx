"use client";

import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { CommentLabel, Pill } from "@/components/ui";

/**
 * 백엔드 API 헬스 체크 — Phase 1.6 검증용 컴포넌트.
 * /api/v1/health 호출해서 캐시 준비/종목수/신호수 표시.
 */
export function HealthStatus() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.health(),
  });

  return (
    <section className="kkj-card-emerald p-5">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <CommentLabel variant="function">api.health()</CommentLabel>
        {data?.cache_ready && <Pill variant="emerald">cache_ready</Pill>}
        {!data?.cache_ready && data && <Pill variant="amber">priming</Pill>}
        {isError && <Pill variant="red">offline</Pill>}
      </div>

      {isLoading && (
        <div className="text-kkj-text-muted text-sm">백엔드 응답 대기 중…</div>
      )}

      {isError && (
        <div className="text-sm text-kkj-red">
          백엔드 연결 실패: {(error as Error).message}
          <div className="mt-2 kkj-comment">
            backend/ 에서 uvicorn 서버가 떠 있는지 확인하세요.
          </div>
        </div>
      )}

      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="kkj-comment">// status</div>
            <div className="font-gmarket-bold text-kkj-emerald-strong">
              {data.status}
            </div>
          </div>
          <div>
            <div className="kkj-comment">// cache</div>
            <div className="font-gmarket-bold">
              {data.cache_ready ? "ready" : "not_ready"}
            </div>
          </div>
          <div>
            <div className="kkj-comment">// tickers</div>
            <div className="font-gmarket-bold font-mono-jb text-kkj-text">
              {data.n_tickers.toLocaleString()}
            </div>
          </div>
          <div>
            <div className="kkj-comment">// signals</div>
            <div className="font-gmarket-bold font-mono-jb text-kkj-text">
              {data.n_signals.toLocaleString()}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
