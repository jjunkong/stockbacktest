"""
테마 → 종목 매핑 로더 + 양방향 조회.

데이터: data/themes.json (수동 큐레이션). Phase 4 키움 연동 후 자동 갱신 교체.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
THEMES_JSON = ROOT / "data" / "themes.json"


class ThemeStore:
    def __init__(self) -> None:
        self.themes: list[dict] = []
        # 종목 → 테마 ID 역인덱스
        self._ticker_to_themes: dict[str, list[str]] = {}
        # 종목이 leader인지 여부 (테마별)
        self._ticker_is_leader: dict[tuple[str, str], bool] = {}

    def load(self) -> None:
        if not THEMES_JSON.exists():
            return
        data = json.loads(THEMES_JSON.read_text(encoding="utf-8"))
        self.themes = data.get("themes", [])
        self._ticker_to_themes.clear()
        self._ticker_is_leader.clear()
        for th in self.themes:
            tid = th["id"]
            for t in th.get("leaders", []):
                self._ticker_to_themes.setdefault(t, []).append(tid)
                self._ticker_is_leader[(t, tid)] = True
            for t in th.get("related", []):
                self._ticker_to_themes.setdefault(t, []).append(tid)
                self._ticker_is_leader[(t, tid)] = False

    def list_themes(self) -> list[dict]:
        """간략한 테마 목록 (id, name, description, n_stocks)."""
        return [
            {
                "id": th["id"],
                "name": th["name"],
                "description": th.get("description", ""),
                "n_leaders": len(th.get("leaders", [])),
                "n_related": len(th.get("related", [])),
            }
            for th in self.themes
        ]

    def get_theme(self, theme_id: str) -> dict | None:
        for th in self.themes:
            if th["id"] == theme_id:
                return th
        return None

    def themes_for_ticker(self, ticker: str) -> list[str]:
        """종목이 속한 테마 이름들."""
        ids = self._ticker_to_themes.get(ticker.zfill(6), [])
        return [
            next((t["name"] for t in self.themes if t["id"] == tid), tid)
            for tid in ids
        ]

    def is_leader(self, ticker: str, theme_id: str) -> bool:
        return self._ticker_is_leader.get((ticker.zfill(6), theme_id), False)


theme_store = ThemeStore()
