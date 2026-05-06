"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

/**
 * React Query Provider — 클라이언트 컴포넌트.
 * 모든 페이지를 감싸기 위해 layout.tsx에서 사용.
 */
export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,           // 1분간 신선
            gcTime: 5 * 60 * 1000,          // 5분 후 가비지 콜렉션
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      }),
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
