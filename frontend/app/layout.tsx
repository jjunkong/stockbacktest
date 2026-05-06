import type { Metadata, Viewport } from "next";
import { Nanum_Gothic, JetBrains_Mono } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import { QueryProvider } from "@/lib/query-provider";

const nanum = Nanum_Gothic({
  variable: "--font-nanum",
  subsets: ["latin"],
  weight: ["400", "700", "800"],
  display: "swap",
});

const mono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Backtest Studio - 보다영어",
  description: "키움 조건검색식 백테스팅 — 신호 발생 후 N일 내 목표 수익률 도달 확률 분석",
  applicationName: "백테스트",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    title: "백테스트",
    statusBarStyle: "black-translucent",
  },
  other: {
    "mobile-web-app-capable": "yes",
  },
};

export const viewport: Viewport = {
  themeColor: "#0F172A",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ko"
      className={`${nanum.variable} ${mono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <QueryProvider>
          <Suspense fallback={<div className="p-8 text-kkj-text-muted">로딩…</div>}>
            {children}
          </Suspense>
        </QueryProvider>
      </body>
    </html>
  );
}
