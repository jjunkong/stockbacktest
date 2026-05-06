/**
 * Backtest Studio 워드마크.
 * 단순한 텍스트 + 그린 점. 학원앱 KKJ 로고와는 다른 톤.
 */
import clsx from "clsx";

interface BrandMarkProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  short?: boolean;  // true이면 "BS"만
}

export function BrandMark({ size = "md", className, short = false }: BrandMarkProps) {
  const text = short ? "BS" : "Backtest Studio";
  const sizeMap = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-xl",
  };

  return (
    <span className={clsx("inline-flex items-center gap-2", className)}>
      <span
        className="block w-2 h-2 rounded-full"
        style={{
          background: "var(--kkj-emerald)",
          boxShadow: "0 0 8px rgba(16, 185, 129, 0.6)",
        }}
        aria-hidden
      />
      <span className={clsx("font-gmarket-bold tracking-tight text-kkj-text", sizeMap[size])}>
        {text}
      </span>
    </span>
  );
}
