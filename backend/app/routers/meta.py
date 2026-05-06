"""메타 정보 — 조건식/시장/진입가 옵션."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.backtest import ENTRY_OPTIONS, ENTRY_LABELS
from app.core.conditions import CONDITIONS
from app.schemas.common import ConditionInfo, MarketInfo, EntryInfo

router = APIRouter(tags=["meta"])

MARKETS = [
    ("all", "전체 (KOSPI+KOSDAQ)"),
    ("KOSPI", "KOSPI"),
    ("KOSDAQ", "KOSDAQ"),
]


@router.get("/conditions", response_model=list[ConditionInfo])
def list_conditions() -> list[ConditionInfo]:
    """등록된 조건식 목록."""
    return [ConditionInfo(id=cid, label=name) for cid, (name, _) in CONDITIONS.items()]


@router.get("/markets", response_model=list[MarketInfo])
def list_markets() -> list[MarketInfo]:
    return [MarketInfo(id=mid, label=label) for mid, label in MARKETS]


@router.get("/entry-options", response_model=list[EntryInfo])
def list_entry_options() -> list[EntryInfo]:
    return [EntryInfo(id=opt, label=ENTRY_LABELS[opt]) for opt in ENTRY_OPTIONS]
